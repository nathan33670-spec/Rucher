"""Routes — Courriels aux adhérents et suivi des campagnes."""

import os
import re
import secrets
import uuid
from datetime import datetime

from fastapi import (APIRouter, Depends, HTTPException, Request, UploadFile,
                     File, Form)
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event, EventRSVP
from app.models.mailing import MailCampaign, MailRecipient, MailAttachment
from app.models.user import User, UserRole, RoleEnum
from app.schemas.mailing import (CampaignOut, CampaignDetail, RecipientOut,
                                 AudienceOut)
from app.utils.app_url import resolve_app_url
from app.utils.audit import log_action
from app.utils.auth import require_roles
from app.utils import mailer
from app.routers.settings import load_mail

router = APIRouter(prefix="/api/mail", tags=["mailing"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
PIECES_DIR = os.path.join(UPLOAD_DIR, "campagnes")

# Une pièce jointe volumineuse fait rejeter tout le message par le serveur du
# destinataire : mieux vaut refuser tout de suite, en le disant.
TAILLE_MAX_PIECE = 8 * 1024 * 1024        # 8 Mo par fichier
TAILLE_MAX_TOTALE = 15 * 1024 * 1024      # 15 Mo pour l'ensemble

# Image d'un pixel, transparente. Servie telle quelle au chargement du
# message : c'est elle qui signale une ouverture.
PIXEL_GIF = bytes.fromhex(
    "47494638396101000100800000000000ffffff21f90401000000002c00000000"
    "010001000002024401003b"
)

AUDIENCES = {
    "all": "Tous les adhérents",
    "admin": "Administrateurs",
    "yard_manager": "Responsables de rucher",
    "treasurer": "Trésoriers",
    "user": "Usagers",
}


async def _destinataires(db: AsyncSession, audience: str,
                         event_id: int | None = None) -> list[User]:
    """Adhérents visés, sans doublon et sans compte sans adresse.

    Une adresse manquante n'est pas une erreur : c'est un compte qui n'a jamais
    renseigné la sienne. On l'écarte et on le dit dans le bilan.
    """
    requete = select(User).where(User.is_active.is_(True),
                                 User.contact_email.isnot(None))

    if audience.startswith("event:"):
        try:
            eid = int(audience.split(":", 1)[1])
        except ValueError:
            raise HTTPException(400, "Événement invalide.")
        requete = requete.join(EventRSVP, EventRSVP.user_id == User.id).where(
            EventRSVP.event_id == eid, EventRSVP.response.in_(("yes", "maybe")))
    elif audience in ("admin", "yard_manager", "treasurer", "user"):
        requete = requete.join(UserRole, UserRole.user_id == User.id).where(
            UserRole.role == RoleEnum(audience))
    elif audience != "all":
        raise HTTPException(400, "Public inconnu.")

    res = await db.execute(requete)
    vus: dict[int, User] = {}
    for u in res.scalars().all():
        vus.setdefault(u.id, u)
    return list(vus.values())


@router.get("/audiences", response_model=list[AudienceOut])
async def list_audiences(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Publics possibles, avec le nombre d'adhérents joignables.

    Le compte est celui des adresses réellement utilisables : annoncer
    « 24 adhérents » pour n'en servir que 11 serait trompeur.
    """
    sorties = []
    for cle, libelle in AUDIENCES.items():
        gens = await _destinataires(db, cle)
        sorties.append(AudienceOut(key=cle, label=libelle, count=len(gens)))

    # Les événements à venir : écrire à ceux qui ont répondu est le cas le
    # plus fréquent après « tout le monde ».
    res = await db.execute(
        select(Event).where(Event.start_at >= datetime.utcnow())
        .order_by(Event.start_at.asc()).limit(10)
    )
    for ev in res.scalars().all():
        gens = await _destinataires(db, f"event:{ev.id}")
        if gens:
            sorties.append(AudienceOut(key=f"event:{ev.id}",
                                       label=f"Inscrits — {ev.title}",
                                       count=len(gens)))
    return sorties


def _html(corps: str, pixel: str | None, app_url: str) -> str:
    """Message mis en forme. Le pixel de suivi ferme le corps s'il est demandé."""
    paragraphes = "".join(
        f'<p style="line-height:1.6;margin:0 0 14px;">{ligne}</p>'
        for ligne in (corps.strip().replace("\r\n", "\n").split("\n\n"))
        if ligne.strip()
    ).replace("\n", "<br/>")
    suivi = (f'<img src="{pixel}" width="1" height="1" alt="" '
             'style="display:block;width:1px;height:1px;border:0;" />') if pixel else ""
    lien = f'<p style="margin-top:26px;"><a href="{app_url}" style="color:#B8860B;">{app_url}</a></p>' if app_url else ""
    return (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'
        'max-width:560px;margin:0 auto;padding:24px;color:#2B2520;">'
        '<div style="text-align:center;font-size:30px;">🐝</div>'
        f'{paragraphes}{lien}'
        '<hr style="border:0;border-top:1px solid #E6DFD4;margin:24px 0 10px;" />'
        '<p style="font-size:12px;color:#8A7F72;">Message envoyé depuis '
        'Rucher Manager par votre association.</p>'
        f'{suivi}</div>'
    )


@router.post("/campaigns", response_model=CampaignDetail, status_code=201)
async def send_campaign(
    request: Request,
    subject: str = Form(...),
    body: str = Form(...),
    audience: str = Form("all"),
    tracking: bool = Form(True),
    files: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Écrit à un groupe d'adhérents, pièces jointes comprises.

    Chaque destinataire reçoit **son** message : c'est ce qui permet le suivi
    des ouvertures, et cela évite d'exposer la liste des adresses à tout le
    monde, ce qu'un envoi groupé en copie ferait.
    """
    subject = (subject or "").strip()
    body = (body or "").strip()
    if not subject:
        raise HTTPException(400, "Le message doit avoir un objet.")
    if not body:
        raise HTTPException(400, "Le message est vide.")

    cfg = await load_mail(db)
    if not mailer.mail_enabled(cfg):
        raise HTTPException(
            503,
            "L'envoi d'e-mails n'est pas configuré : renseignez le serveur SMTP "
            "dans Réglages → Configuration.",
        )

    gens = await _destinataires(db, audience)
    if not gens:
        raise HTTPException(
            400,
            "Aucun destinataire joignable pour ce public : leurs adresses "
            "e-mail ne sont peut-être pas renseignées.",
        )

    # ── Pièces jointes ──
    os.makedirs(PIECES_DIR, exist_ok=True)
    pieces: list[dict] = []
    total = 0
    for f in files or []:
        if not f or not f.filename:
            continue
        contenu = await f.read()
        if len(contenu) > TAILLE_MAX_PIECE:
            raise HTTPException(
                400,
                f"« {f.filename} » dépasse 8 Mo. Les serveurs de messagerie "
                "rejettent les messages trop lourds : réduisez le fichier ou "
                "partagez-le par un lien.",
            )
        total += len(contenu)
        if total > TAILLE_MAX_TOTALE:
            raise HTTPException(
                400,
                "L'ensemble des pièces jointes dépasse 15 Mo. Le message "
                "serait rejeté par la plupart des messageries.",
            )
        nom = os.path.basename(f.filename)
        chemin = os.path.join(PIECES_DIR, f"{uuid.uuid4().hex}_{nom}")
        with open(chemin, "wb") as sortie:
            sortie.write(contenu)
        pieces.append({
            "filename": nom,
            "mime_type": f.content_type or "application/octet-stream",
            "content": contenu,
            "size": len(contenu),
            "file_path": chemin,
        })

    campagne = MailCampaign(
        subject=subject, body=body, audience=audience, tracking=bool(tracking),
        created_by=user.id, sent_at=datetime.utcnow(),
    )
    db.add(campagne)
    await db.flush()

    for p in pieces:
        db.add(MailAttachment(campaign_id=campagne.id, filename=p["filename"],
                              mime_type=p["mime_type"], size=p["size"],
                              file_path=p["file_path"]))

    app_url = resolve_app_url(request, cfg)
    messages = []
    lignes: list[MailRecipient] = []
    for u in gens:
        jeton = secrets.token_urlsafe(24)
        ligne = MailRecipient(
            campaign_id=campagne.id, user_id=u.id,
            name=f"{u.first_name or ''} {u.last_name or ''}".strip() or u.email,
            email=u.contact_email, token=jeton,
        )
        db.add(ligne)
        lignes.append(ligne)
        pixel = f"{app_url}/api/mail/o/{jeton}.gif" if campagne.tracking and app_url else None
        messages.append({
            "to": u.contact_email,
            "subject": subject,
            "html": _html(body, pixel, app_url),
            "text": body + (f"\n\n{app_url}\n" if app_url else "\n"),
            "attachments": [{"filename": p["filename"], "mime_type": p["mime_type"],
                             "content": p["content"]} for p in pieces],
        })

    resultats = await mailer.send_bulk(messages, cfg)
    par_adresse = {r["to"]: r for r in resultats}
    for ligne in lignes:
        r = par_adresse.get(ligne.email, {"ok": False, "error": "non traité"})
        ligne.sent = bool(r.get("ok"))
        ligne.error = None if r.get("ok") else (r.get("error") or "échec")

    campagne.sent_count = sum(1 for l in lignes if l.sent)
    campagne.failed_count = sum(1 for l in lignes if not l.sent)
    await log_action(db, user.id, "mail_campaign", "mail", campagne.id,
                     details=f"{campagne.sent_count} envoyé(s) — {subject[:120]}")
    await db.flush()
    return await _detail(db, campagne)


async def _detail(db: AsyncSession, campagne: MailCampaign) -> CampaignDetail:
    auteur = await db.get(User, campagne.created_by) if campagne.created_by else None
    # Requêtes explicites plutôt que les relations : sur une campagne tout
    # juste créée, le chargement hâtif n'a rien peuplé et l'accès paresseux
    # échoue hors du contexte asynchrone.
    res = await db.execute(
        select(MailRecipient).where(MailRecipient.campaign_id == campagne.id)
        .order_by(func.lower(MailRecipient.name), MailRecipient.id)
    )
    lignes = list(res.scalars().all())
    res = await db.execute(
        select(MailAttachment).where(MailAttachment.campaign_id == campagne.id)
        .order_by(MailAttachment.id)
    )
    pieces_jointes = list(res.scalars().all())
    ouverts = sum(1 for r in lignes if r.first_opened_at)
    return CampaignDetail(
        id=campagne.id, subject=campagne.subject, body=campagne.body,
        audience=campagne.audience,
        audience_label=AUDIENCES.get(campagne.audience, campagne.audience),
        tracking=campagne.tracking, sent_at=campagne.sent_at,
        sent_count=campagne.sent_count, failed_count=campagne.failed_count,
        opened_count=ouverts,
        author_name=(f"{auteur.first_name or ''} {auteur.last_name or ''}".strip()
                     if auteur else None),
        attachments_count=len(pieces_jointes),
        attachments=[{"id": a.id, "filename": a.filename, "size": a.size}
                     for a in pieces_jointes],
        recipients=[RecipientOut(
            id=r.id, name=r.name, email=r.email, sent=r.sent, error=r.error,
            first_opened_at=r.first_opened_at, last_opened_at=r.last_opened_at,
            open_count=r.open_count) for r in lignes],
    )


@router.get("/campaigns", response_model=list[CampaignOut])
async def list_campaigns(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    res = await db.execute(
        select(MailCampaign).order_by(MailCampaign.sent_at.desc())
        .limit(max(1, min(int(limit or 50), 200)))
    )
    sorties = []
    for c in res.scalars().all():
        ouverts = sum(1 for r in c.recipients if r.first_opened_at)
        auteur = await db.get(User, c.created_by) if c.created_by else None
        sorties.append(CampaignOut(
            id=c.id, subject=c.subject, audience=c.audience,
            audience_label=AUDIENCES.get(c.audience, c.audience),
            tracking=c.tracking, sent_at=c.sent_at,
            sent_count=c.sent_count, failed_count=c.failed_count,
            opened_count=ouverts, attachments_count=len(c.attachments),
            author_name=(f"{auteur.first_name or ''} {auteur.last_name or ''}".strip()
                         if auteur else None),
        ))
    return sorties


@router.get("/campaigns/{campaign_id}", response_model=CampaignDetail)
async def get_campaign(
    campaign_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    campagne = await db.get(MailCampaign, campaign_id)
    if not campagne:
        raise HTTPException(404, "Campagne introuvable")
    return await _detail(db, campagne)


@router.get("/campaigns/{campaign_id}/attachments/{attachment_id}")
async def download_attachment(
    campaign_id: int,
    attachment_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Récupère une pièce jointe déjà envoyée.

    Le fichier est stocké dans le volume partagé avec nginx, mais le serveur
    web refuse ce dossier : le seul chemin d'accès est cette route, qui exige
    un administrateur. Savoir ce qu'on a envoyé six mois plus tôt fait partie
    de la trace d'une campagne.
    """
    piece = await db.get(MailAttachment, attachment_id)
    if not piece or piece.campaign_id != campaign_id:
        raise HTTPException(404, "Pièce jointe introuvable")

    # Le chemin vient de la base, mais on vérifie tout de même qu'il reste
    # dans le dossier des campagnes : une donnée en base n'est pas une
    # garantie suffisante pour ouvrir un fichier arbitraire.
    chemin = os.path.realpath(piece.file_path or "")
    if not chemin.startswith(os.path.realpath(PIECES_DIR) + os.sep) \
            or not os.path.isfile(chemin):
        raise HTTPException(
            404,
            "Le fichier n'est plus disponible sur le serveur. Le message, lui, "
            "est bien parti avec sa pièce jointe.",
        )

    with open(chemin, "rb") as f:
        contenu = f.read()
    nom = piece.filename.replace('"', "")
    return Response(
        content=contenu,
        media_type=piece.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{nom}"'},
    )


@router.get("/o/{token}.gif")
async def track_open(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Pixel de suivi : **publiquement accessible**, et c'est nécessaire.

    L'image est chargée par la messagerie du destinataire, qui n'est pas
    connectée à l'application. Le jeton est tiré au hasard et ne révèle rien :
    il ne permet ni de remonter à une adresse, ni d'en deviner une autre.

    L'image est toujours renvoyée, même sur un jeton inconnu — répondre 404
    dessinerait un carré cassé dans le message.
    """
    if re.fullmatch(r"[A-Za-z0-9_\-]{10,64}", token or ""):
        res = await db.execute(
            select(MailRecipient).where(MailRecipient.token == token)
        )
        ligne = res.scalar_one_or_none()
        if ligne is not None:
            maintenant = datetime.utcnow()
            if ligne.first_opened_at is None:
                ligne.first_opened_at = maintenant
            ligne.last_opened_at = maintenant
            ligne.open_count = (ligne.open_count or 0) + 1

    return Response(
        content=PIXEL_GIF,
        media_type="image/gif",
        headers={
            # Sans cela, la messagerie sert l'image depuis son cache et les
            # lectures suivantes ne remontent jamais.
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )
