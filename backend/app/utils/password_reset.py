"""Réinitialisation de mot de passe en autonomie, par e-mail.

Choix de sécurité :

- le jeton est tiré au hasard (``secrets``) et **seule son empreinte SHA-256**
  est stockée : une fuite de la base ne permet pas de rejouer un lien valide ;
- il est à usage unique et expire vite ; valider une demande révoque toutes
  les autres demandes en cours pour ce compte ;
- la réponse à une demande est **toujours la même**, que le compte existe ou
  non : sinon le formulaire permettrait de découvrir qui est inscrit ;
- la validation incrémente ``token_version``, ce qui déconnecte immédiatement
  tous les appareils — c'est le comportement attendu quand on soupçonne que
  son mot de passe est compromis.
"""

import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import select, update

from app.models.user import User, PasswordResetToken

# Durée de validité d'un lien. Assez court pour limiter la fenêtre de reprise
# d'une boîte mail compromise, assez long pour relever ses mails tranquillement.
TOKEN_TTL = timedelta(hours=1)

# Garde-fous anti-abus : on ne renvoie pas un lien toutes les secondes, et un
# compte ne peut pas servir à inonder une boîte mail.
MIN_INTERVAL = timedelta(minutes=1)
MAX_PER_HOUR = 5


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_token() -> tuple[str, str]:
    """(jeton en clair pour l'e-mail, empreinte à stocker)."""
    token = secrets.token_urlsafe(32)
    return token, hash_token(token)


async def find_account(db, identifier: str) -> User | None:
    """Compte correspondant à un identifiant de connexion **ou** une adresse.

    La comparaison est insensible à la casse : personne ne retient si son
    identifiant a été saisi avec une majuscule.
    """
    ident = (identifier or "").strip().lower()
    if not ident:
        return None
    from sqlalchemy import func, or_
    res = await db.execute(
        select(User).where(
            or_(func.lower(User.email) == ident,
                func.lower(User.contact_email) == ident)
        ).limit(1)
    )
    return res.scalar_one_or_none()


async def too_many_requests(db, user: User) -> bool:
    """Vrai si ce compte a déjà demandé trop de liens récemment."""
    now = datetime.utcnow()
    res = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id,
               PasswordResetToken.created_at >= now - timedelta(hours=1))
        .order_by(PasswordResetToken.created_at.desc())
    )
    recent = list(res.scalars().all())
    if len(recent) >= MAX_PER_HOUR:
        return True
    return bool(recent and recent[0].created_at and now - recent[0].created_at < MIN_INTERVAL)


async def create_token(db, user: User) -> str:
    """Crée un jeton et renvoie sa version en clair (à ne jamais stocker)."""
    token, digest = new_token()
    db.add(PasswordResetToken(
        user_id=user.id,
        token_hash=digest,
        expires_at=datetime.utcnow() + TOKEN_TTL,
    ))
    await db.flush()
    return token


async def consume_token(db, token: str) -> User | None:
    """Valide un jeton et renvoie le compte associé, ou None.

    Le jeton est marqué consommé et toutes les autres demandes en cours du
    même compte sont annulées : après une réinitialisation, aucun ancien lien
    ne doit rester actionnable.
    """
    digest = hash_token(token or "")
    if not digest:
        return None
    res = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.token_hash == digest).limit(1)
    )
    row = res.scalar_one_or_none()
    now = datetime.utcnow()
    if not row or row.used_at is not None or row.expires_at < now:
        return None

    user = await db.get(User, row.user_id)
    if not user or not user.is_active:
        return None

    row.used_at = now
    await db.execute(
        update(PasswordResetToken)
        .where(PasswordResetToken.user_id == user.id,
               PasswordResetToken.used_at.is_(None))
        .values(used_at=now)
    )
    return user


async def token_is_valid(db, token: str) -> bool:
    """Vérifie un jeton **sans le consommer** (affichage du formulaire)."""
    res = await db.execute(
        select(PasswordResetToken)
        .where(PasswordResetToken.token_hash == hash_token(token or "")).limit(1)
    )
    row = res.scalar_one_or_none()
    if not row or row.used_at is not None or row.expires_at < datetime.utcnow():
        return False
    user = await db.get(User, row.user_id)
    return bool(user and user.is_active)


def build_email(user: User, link: str) -> tuple[str, str, str]:
    """(sujet, html, texte) du message de réinitialisation."""
    who = f"{user.first_name or ''}".strip() or user.email
    minutes = int(TOKEN_TTL.total_seconds() // 60)
    subject = "Rucher Manager — réinitialisation de votre mot de passe"
    html = (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'
        'max-width:520px;margin:0 auto;padding:24px;color:#2B2520;">'
        '<div style="text-align:center;font-size:30px;">🐝</div>'
        f'<h2 style="text-align:center;font-size:19px;">Bonjour {who},</h2>'
        '<p style="line-height:1.6;">Vous avez demandé à réinitialiser votre mot '
        'de passe Rucher Manager. Cliquez sur le bouton ci-dessous :</p>'
        '<p style="text-align:center;margin:28px 0;">'
        f'<a href="{link}" style="background:#B8860B;color:#fff;text-decoration:none;'
        'padding:13px 26px;border-radius:8px;display:inline-block;font-weight:600;">'
        'Choisir un nouveau mot de passe</a></p>'
        f'<p style="line-height:1.6;font-size:14px;color:#4E443A;">Ce lien est '
        f'valable <b>{minutes} minutes</b> et ne fonctionne qu\'une seule fois. '
        'Une fois le mot de passe changé, vous serez déconnecté de tous vos '
        'appareils.</p>'
        '<p style="line-height:1.6;font-size:14px;color:#4E443A;">Si vous n\'êtes '
        'pas à l\'origine de cette demande, ignorez ce message : votre mot de '
        'passe actuel reste valable.</p>'
        '<p style="font-size:12px;color:#8A7F72;word-break:break-all;">'
        f'Si le bouton ne fonctionne pas, copiez ce lien : {link}</p></div>'
    )
    text = (
        f"Bonjour {who},\n\n"
        "Vous avez demandé à réinitialiser votre mot de passe Rucher Manager.\n"
        f"Ouvrez ce lien pour choisir un nouveau mot de passe :\n\n{link}\n\n"
        f"Ce lien est valable {minutes} minutes et ne fonctionne qu'une seule fois.\n"
        "Une fois le mot de passe changé, vous serez déconnecté de tous vos appareils.\n\n"
        "Si vous n'êtes pas à l'origine de cette demande, ignorez ce message : "
        "votre mot de passe actuel reste valable.\n"
    )
    return subject, html, text
