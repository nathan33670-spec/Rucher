"""Routes — Courriels aux adhérents et suivi des campagnes."""

import os
import re
from html import escape
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import (APIRouter, Depends, HTTPException, Request, UploadFile,
                     File, Form)
from fastapi.responses import Response, RedirectResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.event import Event, EventRSVP
from app.models.mailing import (MailCampaign, MailRecipient, MailAttachment,
                                MailLink)
from app.models.user import User, UserRole, RoleEnum
from app.schemas.mailing import (CampaignOut, CampaignDetail, RecipientOut,
                                 AudienceOut)
from app.utils.app_url import resolve_app_url
from app.utils import mail_html
from app.utils.audit import log_action
from app.utils.auth import require_roles
from app.utils import mailer
from app.routers.settings import load_mail

router = APIRouter(prefix="/api/mail", tags=["mailing"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
PIECES_DIR = os.path.join(UPLOAD_DIR, "campagnes")

# Une pièce jointe volumineuse fait rejeter tout le message par le serveur du
# destinataire. Plutôt que de refuser le fichier, on change de moyen : au-delà
# du seuil, il reste sur l'application et le message ne porte qu'un lien.
SEUIL_PIECE_JOINTE = 5 * 1024 * 1024      # 5 Mo : au-delà, on héberge
TAILLE_MAX_TOTALE = 15 * 1024 * 1024      # 15 Mo de pièces réellement jointes
TAILLE_MAX_HEBERGEE = 50 * 1024 * 1024    # 50 Mo par fichier hébergé
JOURS_VALIDITE_LIEN = 90                  # durée de vie d'un lien de téléchargement

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


_HREF = re.compile(r'href="([^"]+)"')


def _urls_du_corps(html: str) -> list[str]:
    """Adresses des liens du message, dans leur ordre d'apparition."""
    return _HREF.findall(html or "")


def _pister_liens(html: str, app_url: str, jeton: str) -> str:
    """Fait passer chaque lien par la redirection propre à ce destinataire.

    Un clic est une preuve d'ouverture bien plus solide que le pixel : il ne
    peut pas être déclenché par un préchargement d'images, et il fonctionne
    même chez qui bloque les images. C'est ce qui rattrape l'essentiel de ce
    que le pixel ne voit pas.
    """
    if not app_url or not jeton:
        return html
    compteur = {"n": -1}

    def remplace(m):
        compteur["n"] += 1
        return f'href="{app_url}/api/mail/c/{jeton}/{compteur["n"]}"'

    return _HREF.sub(remplace, html or "")


def _bloc_fichiers(fichiers: list[dict]) -> str:
    """Encart listant les fichiers déposés sur l'application."""
    if not fichiers:
        return ""
    lignes = "".join(
        '<li style="margin-bottom:6px;">'
        f'<a href="{f["url"]}" style="color:#B8860B;">{escape(f["filename"])}</a>'
        f' <span style="color:#8A7F72;">({_taille_lisible(f["size"])})</span>'
        "</li>"
        for f in fichiers
    )
    return (
        '<div style="background:#FAF6EF;border:1px solid #E6DFD4;border-radius:8px;'
        'padding:14px 18px;margin:22px 0;">'
        '<p style="margin:0 0 8px;font-weight:600;">📎 Fichiers à télécharger</p>'
        f'<ul style="margin:0;padding-left:20px;">{lignes}</ul>'
        '<p style="margin:10px 0 0;font-size:12px;color:#8A7F72;">'
        f'Ces liens restent valables {JOURS_VALIDITE_LIEN} jours.</p>'
        "</div>"
    )


def _taille_lisible(octets: int) -> str:
    if octets >= 1024 * 1024:
        return f"{octets / (1024 * 1024):.1f} Mo".replace(".", ",")
    return f"{max(1, round(octets / 1024))} Ko"


def _html(corps_html: str, pixel: str | None, app_url: str,
          fichiers: list[dict] | None = None) -> str:
    """Message complet. Le pixel de suivi ferme le corps s'il est demandé."""
    suivi = (f'<img src="{pixel}" width="1" height="1" alt="" '
             'style="display:block;width:1px;height:1px;border:0;" />') if pixel else ""
    lien = (f'<p style="margin-top:26px;"><a href="{app_url}" '
            f'style="color:#B8860B;">{app_url}</a></p>') if app_url else ""
    return (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'
        'max-width:560px;margin:0 auto;padding:24px;color:#2B2520;line-height:1.6;">'
        '<div style="text-align:center;font-size:30px;">🐝</div>'
        f'{corps_html}{_bloc_fichiers(fichiers or [])}{lien}'
        '<hr style="border:0;border-top:1px solid #E6DFD4;margin:24px 0 10px;" />'
        '<p style="font-size:12px;color:#8A7F72;">Message envoyé depuis '
        'Rucher Manager par votre association.</p>'
        f'{suivi}</div>'
    )


def _texte_complet(corps_texte: str, app_url: str, fichiers: list[dict] | None) -> str:
    """Partie texte du message, liens de téléchargement compris.

    Qui lit en texte seul doit pouvoir récupérer les fichiers lui aussi :
    sans cela, l'encart HTML serait sa seule chance de les voir.
    """
    parties = [corps_texte]
    if fichiers:
        lignes = "\n".join(
            f"- {f['filename']} ({_taille_lisible(f['size'])}) : {f['url']}"
            for f in fichiers
        )
        parties.append(f"Fichiers à télécharger (valables {JOURS_VALIDITE_LIEN} jours) :\n{lignes}")
    if app_url:
        parties.append(app_url)
    return "\n\n".join(parties) + "\n"


def _corps_propre(body: str, body_html: str | None) -> tuple[str, str]:
    """(HTML désinfecté, texte seul) à partir de ce que l'éditeur a produit.

    Sans ``body_html`` — anciennes campagnes, ou saisie en texte simple — le
    texte est converti en paragraphes plutôt qu'affiché d'un seul bloc.
    """
    if body_html and body_html.strip():
        propre = mail_html.nettoyer(body_html)
        texte = mail_html.en_texte(propre)
        if texte.strip():
            return propre, texte
    return mail_html.depuis_texte(body), (body or "").strip()


async def _recevoir_fichiers(files) -> list[dict]:
    """Enregistre les fichiers reçus et décide lesquels sont joints au message.

    Au-delà du seuil, un fichier n'est pas joint mais déposé sur
    l'application : joindre 30 Mo à un courriel, c'est le faire rejeter par
    presque tous les serveurs de messagerie.
    """
    os.makedirs(PIECES_DIR, exist_ok=True)
    pieces: list[dict] = []
    total_joint = 0
    for f in files or []:
        if not f or not f.filename:
            continue
        contenu = await f.read()
        if len(contenu) > TAILLE_MAX_HEBERGEE:
            raise HTTPException(
                400,
                f"« {f.filename} » dépasse {TAILLE_MAX_HEBERGEE // (1024 * 1024)} Mo, "
                "la taille maximale acceptée même en dépôt sur l'application.",
            )
        heberge = len(contenu) > SEUIL_PIECE_JOINTE
        if not heberge:
            total_joint += len(contenu)
            if total_joint > TAILLE_MAX_TOTALE:
                raise HTTPException(
                    400,
                    "L'ensemble des pièces réellement jointes dépasse 15 Mo. "
                    "Le message serait rejeté par la plupart des messageries : "
                    "envoyez les fichiers les plus lourds séparément, ils "
                    "seront déposés sur l'application.",
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
            "hosted": heberge,
        })
    return pieces


@router.post("/campaigns", response_model=CampaignDetail, status_code=201)
async def send_campaign(
    request: Request,
    subject: str = Form(...),
    body: str = Form(...),
    body_html: str = Form(""),
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
    # Le corps arrive soit en texte, soit mis en forme par l'éditeur : c'est
    # ce qui en ressort qui fait foi. Juger sur « body » seul rejetait tout
    # message écrit dans l'éditeur enrichi.
    corps_html, corps_texte = _corps_propre(body, body_html)
    if not corps_texte.strip():
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

    pieces = await _recevoir_fichiers(files)

    campagne = MailCampaign(
        subject=subject, body=corps_texte, body_html=corps_html,
        audience=audience, tracking=bool(tracking),
        created_by=user.id, sent_at=datetime.utcnow(),
    )
    db.add(campagne)
    await db.flush()

    app_url = resolve_app_url(request, cfg)
    expire = datetime.utcnow() + timedelta(days=JOURS_VALIDITE_LIEN)
    fichiers_lies: list[dict] = []
    for p in pieces:
        jeton_f = secrets.token_urlsafe(24) if p["hosted"] else None
        db.add(MailAttachment(
            campaign_id=campagne.id, filename=p["filename"],
            mime_type=p["mime_type"], size=p["size"], file_path=p["file_path"],
            hosted=p["hosted"], token=jeton_f,
            expires_at=expire if p["hosted"] else None,
        ))
        if p["hosted"]:
            fichiers_lies.append({
                "filename": p["filename"], "size": p["size"],
                "url": f"{app_url}/api/mail/f/{jeton_f}",
            })

    # Le corps final (encart des fichiers compris) sert de référence pour les
    # liens : leur rang doit être le même ici et dans le message envoyé.
    corps_complet = _html(corps_html, None, app_url, fichiers_lies)
    for rang, url in enumerate(_urls_du_corps(corps_complet)):
        db.add(MailLink(campaign_id=campagne.id, position=rang, url=url))
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
        html = _html(corps_html, pixel, app_url, fichiers_lies)
        if campagne.tracking:
            html = _pister_liens(html, app_url, jeton)
        messages.append({
            "to": u.contact_email,
            "subject": subject,
            "html": html,
            "text": _texte_complet(corps_texte, app_url, fichiers_lies),
            "attachments": [{"filename": p["filename"], "mime_type": p["mime_type"],
                             "content": p["content"]}
                            for p in pieces if not p["hosted"]],
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
    clics = sum(1 for r in lignes if r.first_clicked_at)
    return CampaignDetail(
        id=campagne.id, subject=campagne.subject, body=campagne.body,
        body_html=campagne.body_html, clicked_count=clics,
        audience=campagne.audience,
        audience_label=AUDIENCES.get(campagne.audience, campagne.audience),
        tracking=campagne.tracking, sent_at=campagne.sent_at,
        sent_count=campagne.sent_count, failed_count=campagne.failed_count,
        opened_count=ouverts,
        author_name=(f"{auteur.first_name or ''} {auteur.last_name or ''}".strip()
                     if auteur else None),
        attachments_count=len(pieces_jointes),
        attachments=[{"id": a.id, "filename": a.filename, "size": a.size,
                      "hosted": bool(a.hosted),
                      "download_count": a.download_count or 0,
                      "expires_at": a.expires_at.isoformat() if a.expires_at else None}
                     for a in pieces_jointes],
        recipients=[RecipientOut(
            id=r.id, name=r.name, email=r.email, sent=r.sent, error=r.error,
            first_opened_at=r.first_opened_at, last_opened_at=r.last_opened_at,
            open_count=r.open_count, first_clicked_at=r.first_clicked_at,
            click_count=r.click_count or 0) for r in lignes],
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
        clics = sum(1 for r in c.recipients if r.first_clicked_at)
        auteur = await db.get(User, c.created_by) if c.created_by else None
        sorties.append(CampaignOut(
            id=c.id, subject=c.subject, audience=c.audience,
            audience_label=AUDIENCES.get(c.audience, c.audience),
            tracking=c.tracking, sent_at=c.sent_at,
            sent_count=c.sent_count, failed_count=c.failed_count,
            opened_count=ouverts, clicked_count=clics,
            attachments_count=len(c.attachments),
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


@router.post("/preview")
async def preview_campaign(
    request: Request,
    subject: str = Form(...),
    body: str = Form(""),
    body_html: str = Form(""),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Rend le message tel qu'il partira, en passant par la même tuyauterie.

    Un aperçu reconstitué autrement finirait par mentir : c'est bien le HTML
    désinfecté et mis en page ici qui est envoyé.
    """
    cfg = await load_mail(db)
    app_url = resolve_app_url(request, cfg)
    corps_html, corps_texte = _corps_propre(body, body_html)
    if not corps_texte.strip():
        raise HTTPException(400, "Le message est vide : rien à prévisualiser.")
    return {
        "subject": (subject or "").strip(),
        "html": _html(corps_html, None, app_url),
        "text": _texte_complet(corps_texte, app_url, []),
    }


@router.post("/test")
async def test_campaign(
    request: Request,
    subject: str = Form(...),
    body: str = Form(""),
    body_html: str = Form(""),
    files: list[UploadFile] = File(default=[]),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Envoie le message à soi-même, sans rien enregistrer.

    Aucune campagne n'est créée, aucun suivi n'est posé : un essai ne doit pas
    venir gonfler les statistiques ni l'historique.
    """
    subject = (subject or "").strip()
    if not subject:
        raise HTTPException(400, "Le message doit avoir un objet.")
    destinataire = (user.contact_email or "").strip()
    if not destinataire:
        raise HTTPException(
            400,
            "Votre fiche ne porte pas d'adresse e-mail : renseignez-la dans "
            "Utilisateurs pour pouvoir vous envoyer un essai.",
        )

    cfg = await load_mail(db)
    if not mailer.mail_enabled(cfg):
        raise HTTPException(
            503,
            "L'envoi d'e-mails n'est pas configuré : renseignez le serveur SMTP "
            "dans Réglages → Configuration.",
        )

    corps_html, corps_texte = _corps_propre(body, body_html)
    if not corps_texte.strip():
        raise HTTPException(400, "Le message est vide.")

    pieces = await _recevoir_fichiers(files)
    app_url = resolve_app_url(request, cfg)
    # Les fichiers lourds ne sont pas encore déposés : l'essai les annonce sans
    # lien plutôt que d'en fabriquer un qui ne mènerait nulle part.
    annonces = [{"filename": p["filename"], "size": p["size"], "url": app_url or "#"}
                for p in pieces if p["hosted"]]
    html = _html(corps_html, None, app_url, annonces)
    resultats = await mailer.send_bulk([{
        "to": destinataire,
        "subject": f"[Essai] {subject}",
        "html": html,
        "text": _texte_complet(corps_texte, app_url, annonces),
        "attachments": [{"filename": p["filename"], "mime_type": p["mime_type"],
                         "content": p["content"]}
                        for p in pieces if not p["hosted"]],
    }], cfg)

    # Les fichiers de l'essai ne servent plus à rien : on ne les garde pas.
    for p in pieces:
        try:
            os.remove(p["file_path"])
        except OSError:
            pass

    r = resultats[0] if resultats else {"ok": False, "error": "aucun envoi"}
    if not r.get("ok"):
        raise HTTPException(502, f"L'essai n'est pas parti : {r.get('error') or 'échec'}")
    return {"to": destinataire, "hosted_pending": len(annonces)}


@router.get("/c/{token}/{position}")
async def track_click(
    token: str,
    position: int,
    db: AsyncSession = Depends(get_db),
):
    """Redirection de suivi : compte le clic, puis mène au lien d'origine.

    **Publique par nécessité** : c'est le navigateur du destinataire qui
    l'appelle, sans session. La destination n'est jamais portée par l'URL mais
    lue en base — un lien de redirection qui transporte sa cible se prête à
    l'hameçonnage sous le nom de l'association.
    """
    if not re.fullmatch(r"[A-Za-z0-9_\-]{10,64}", token or ""):
        raise HTTPException(404, "Lien inconnu")
    res = await db.execute(select(MailRecipient).where(MailRecipient.token == token))
    ligne = res.scalar_one_or_none()
    if not ligne:
        raise HTTPException(404, "Lien inconnu")
    res = await db.execute(
        select(MailLink).where(MailLink.campaign_id == ligne.campaign_id,
                               MailLink.position == position)
    )
    lien = res.scalar_one_or_none()
    if not lien:
        raise HTTPException(404, "Lien inconnu")

    maintenant = datetime.utcnow()
    lien.click_count = (lien.click_count or 0) + 1
    ligne.click_count = (ligne.click_count or 0) + 1
    ligne.last_clicked_at = maintenant
    if not ligne.first_clicked_at:
        ligne.first_clicked_at = maintenant
    # Un clic prouve l'ouverture, même si le pixel n'a jamais été chargé :
    # sans cela, une messagerie bloquant les images ferait disparaître une
    # lecture pourtant certaine.
    ligne.last_opened_at = maintenant
    if not ligne.first_opened_at:
        ligne.first_opened_at = maintenant
        ligne.open_count = (ligne.open_count or 0) + 1
    await db.commit()
    return RedirectResponse(lien.url, status_code=302)


@router.get("/f/{token}")
async def download_hosted(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Fichier déposé sur l'application, servi par lien secret.

    Le jeton est long et tiré au hasard ; le lien cesse de fonctionner au bout
    de quelques mois. Il n'exige pas de connexion — un adhérent qui ne
    retrouve pas son mot de passe doit tout de même pouvoir lire la pièce
    jointe — mais quiconque le reçoit peut le transmettre : c'est le prix de
    cette facilité, et il vaut mieux le savoir avant d'y déposer un document
    confidentiel.
    """
    if not re.fullmatch(r"[A-Za-z0-9_\-]{10,64}", token or ""):
        raise HTTPException(404, "Fichier introuvable")
    res = await db.execute(
        select(MailAttachment).where(MailAttachment.token == token,
                                     MailAttachment.hosted.is_(True))
    )
    piece = res.scalar_one_or_none()
    if not piece:
        raise HTTPException(404, "Fichier introuvable")
    if piece.expires_at and datetime.utcnow() > piece.expires_at:
        raise HTTPException(
            410,
            "Ce lien de téléchargement a expiré. Demandez à l'association de "
            "vous renvoyer le fichier.",
        )
    chemin = os.path.realpath(piece.file_path or "")
    if not chemin.startswith(os.path.realpath(PIECES_DIR) + os.sep) \
            or not os.path.isfile(chemin):
        raise HTTPException(404, "Le fichier n'est plus disponible sur le serveur.")

    piece.download_count = (piece.download_count or 0) + 1
    await db.commit()
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
