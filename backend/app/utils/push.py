"""Notifications push web (VAPID + pywebpush).

- Les clés VAPID sont générées une fois et persistées dans app_settings.
- L'envoi est fait en tâche de fond (pywebpush est synchrone → asyncio.to_thread).
- Les abonnements expirés (404/410) sont supprimés automatiquement.
"""

import json
import base64
import asyncio
from datetime import datetime

from sqlalchemy import select, delete, or_, and_
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from pywebpush import webpush, WebPushException
from py_vapid import Vapid02, _check_sub

from app.database import async_session
from app.models.notification import AppSetting, PushSubscription, NotificationPref
from app.config import get_settings

# Catégories notifiables (doivent correspondre aux colonnes de NotificationPref)
CATEGORIES = {"visits", "inventory", "alerts", "sanitary", "treasury", "events"}


def _generate_keys():
    priv = ec.generate_private_key(ec.SECP256R1())
    priv_pem = priv.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    ).decode()
    raw_pub = priv.public_key().public_bytes(
        serialization.Encoding.X962,
        serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64 = base64.urlsafe_b64encode(raw_pub).rstrip(b"=").decode()
    return priv_pem, pub_b64


async def get_or_create_vapid(db):
    """Renvoie (private_pem, public_b64), en générant/persistant si nécessaire."""
    res = await db.execute(
        select(AppSetting).where(AppSetting.key.in_(["vapid_private", "vapid_public"]))
    )
    rows = {r.key: r.value for r in res.scalars().all()}
    if rows.get("vapid_private") and rows.get("vapid_public"):
        return rows["vapid_private"], rows["vapid_public"]
    priv, pub = _generate_keys()
    db.add(AppSetting(key="vapid_private", value=priv))
    db.add(AppSetting(key="vapid_public", value=pub))
    await db.flush()
    return priv, pub


# Contact exigé par le protocole VAPID (revendication « sub » du jeton). Le
# service de push le rejette s'il ne ressemble pas à une adresse mailto: ou à
# une URL https — et py_vapid refuse alors de signer.
FALLBACK_SUBJECT = "mailto:admin@rucher.local"


def _valid_subject(value: str) -> bool:
    return bool(value) and bool(_check_sub(value))


async def resolve_vapid_subject(db=None) -> str:
    """Contact VAPID valide, quelle que soit la configuration du serveur.

    L'identifiant du premier administrateur est un **nom de connexion**
    (« paulin », « admin »…), pas une adresse : « mailto:admin » ne passait pas
    la validation de py_vapid, qui levait alors « Missing 'sub' from claims ».
    Résultat : *aucune* notification n'était jamais délivrée, sur toutes les
    installations où l'identifiant n'était pas une vraie adresse e-mail.

    On prend donc la première valeur réellement exploitable : l'expéditeur des
    e-mails, l'adresse du site, l'identifiant admin s'il est une adresse, puis
    un contact générique valide.
    """
    s = get_settings()
    candidates = []

    # Réglages saisis dans l'application (prioritaires sur l'environnement).
    if db is not None:
        row = await db.get(AppSetting, "mail_settings")
        if row:
            try:
                stored = json.loads(row.value)
                candidates += [stored.get("smtp_from"), stored.get("smtp_user"),
                               stored.get("app_base_url")]
            except Exception:
                pass

    candidates += [s.smtp_from, s.smtp_user, s.app_base_url, s.first_admin_email]

    for raw in candidates:
        raw = (raw or "").strip()
        if not raw:
            continue
        value = raw if raw.startswith(("mailto:", "http://", "https://")) else "mailto:" + raw
        # Une URL http:// n'est pas acceptée par la spécification : on l'ignore.
        if _valid_subject(value):
            return value

    return FALLBACK_SUBJECT


def _send_one(sub_row, payload: str, vapid: Vapid02, subject: str):
    # pywebpush attend soit une instance Vapid, soit du base64-DER — surtout PAS
    # un PEM (Vapid.from_string() ferait un from_der et lèverait une erreur ASN.1,
    # avalée plus bas → aucune notification n'était jamais envoyée).
    webpush(
        subscription_info={
            "endpoint": sub_row.endpoint,
            "keys": {"p256dh": sub_row.p256dh, "auth": sub_row.auth},
        },
        data=payload,
        vapid_private_key=vapid,
        vapid_claims={"sub": subject},
        timeout=10,
    )


# Dernier résultat d'envoi, exposé au diagnostic administrateur : un envoi qui
# échoue en silence est indiscernable d'un envoi qui n'a jamais été déclenché.
LAST_RESULT: dict = {}


async def _dispatch(subs, title, body, url):
    """Envoie le message à une liste d'abonnements (ouvre sa propre session)."""
    if not subs:
        LAST_RESULT.update({
            "at": datetime.utcnow().isoformat(timespec="seconds"),
            "title": title, "targets": 0, "sent": 0, "failed": 0,
            "removed": 0, "error": "aucun appareil abonné concerné",
        })
        return 0
    async with async_session() as db:
        priv, _pub = await get_or_create_vapid(db)
        subject = await resolve_vapid_subject(db)
        await db.commit()
    payload = json.dumps({"title": title, "body": body, "url": url or "/app"})
    vapid = Vapid02.from_pem(priv.encode())
    to_delete = []
    sent = 0
    failed = 0
    last_error = None
    for s in subs:
        try:
            await asyncio.to_thread(_send_one, s, payload, vapid, subject)
            sent += 1
        except WebPushException as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in (404, 410):
                # Abonnement révoqué côté navigateur : on le retire du parc.
                to_delete.append(s.id)
            else:
                # Refus du service de push (clé, quota, panne) ou point de
                # terminaison injoignable : c'était jusqu'ici avalé en silence,
                # donc indiagnosticable depuis l'application.
                failed += 1
                last_error = f"{code or 'sans réponse'} — {e}"
        except Exception as e:
            # Ne jamais interrompre l'envoi aux autres appareils, mais laisser
            # une trace : un échec silencieux avait déjà masqué une clé VAPID
            # invalide, sans aucun signe côté serveur.
            failed += 1
            last_error = str(e)
    if failed:
        print(f"⚠️  Push : {failed} envoi(s) en échec sur {len(subs)} — dernier : {last_error}")
    if to_delete:
        async with async_session() as db:
            await db.execute(delete(PushSubscription).where(PushSubscription.id.in_(to_delete)))
            await db.commit()
        print(f"ℹ️  Push : {len(to_delete)} abonnement(s) périmé(s) supprimé(s)")
    LAST_RESULT.update({
        "at": datetime.utcnow().isoformat(timespec="seconds"),
        "title": title, "targets": len(subs), "sent": sent, "failed": failed,
        "removed": len(to_delete), "error": str(last_error) if last_error else None,
        "subject": subject,
    })
    return sent


async def send_push_to_category(category: str, title: str, body: str,
                                url: str = "/app", exclude_user_id: int = None):
    """Notifie les utilisateurs abonnés ayant activé cette catégorie.

    ``exclude_user_id`` évite de notifier l'auteur de l'action : recevoir une
    alerte pour ce que l'on vient soi-même de saisir noyait les notifications
    réellement utiles.
    """
    if category not in CATEGORIES:
        print(f"⚠️  Push : catégorie inconnue « {category} », message ignoré")
        return 0
    async with async_session() as db:
        field = getattr(NotificationPref, category)
        # On part des abonnements, pas des préférences : un appareil abonné
        # dont la ligne de préférences manque (échec d'écriture, base
        # antérieure à une colonne) ne recevait plus jamais rien, en silence.
        # L'absence de préférences vaut « tout activé », comme les valeurs par
        # défaut du modèle.
        res = await db.execute(
            select(PushSubscription)
            .outerjoin(NotificationPref,
                       NotificationPref.user_id == PushSubscription.user_id)
            .where(
                or_(NotificationPref.user_id.is_(None),
                    and_(NotificationPref.enabled.is_(True), field.is_(True))),
            )
        )
        subs = [s for s in res.scalars().all() if s.user_id != exclude_user_id]
    return await _dispatch(subs, title, body, url)


async def send_push_to_users(user_ids, title: str, body: str,
                             url: str = "/app", exclude_user_id: int = None):
    """Notifie des utilisateurs précis (ex. les responsables d'une ruche).

    Ces messages sont nominatifs : ils passent outre les préférences de
    catégorie, mais respectent l'interrupteur général de chaque personne.
    """
    targets = {int(u) for u in user_ids if u and u != exclude_user_id}
    if not targets:
        return 0
    async with async_session() as db:
        # Seul un refus explicite fait taire une notification nominative.
        res = await db.execute(
            select(NotificationPref.user_id).where(
                NotificationPref.user_id.in_(targets),
                NotificationPref.enabled.is_(False),
            )
        )
        targets -= set(res.scalars().all())
        if not targets:
            return await _dispatch([], title, body, url)
        res = await db.execute(
            select(PushSubscription).where(PushSubscription.user_id.in_(targets))
        )
        subs = list(res.scalars().all())
    return await _dispatch(subs, title, body, url)


async def send_push_to_user(user_id: int, title: str, body: str, url: str = "/app"):
    """Notifie uniquement les appareils d'un utilisateur (ex. notification de test)."""
    async with async_session() as db:
        res = await db.execute(
            select(PushSubscription).where(PushSubscription.user_id == user_id)
        )
        subs = list(res.scalars().all())
    return await _dispatch(subs, title, body, url)


_bg_tasks = set()


def notify(category: str, title: str, body: str, url: str = "/app",
           exclude_user_id: int = None):
    """Déclenche l'envoi sans bloquer la requête (fire-and-forget)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        print(f"⚠️  Push : aucune boucle d'exécution, « {title} » non envoyé")
        return
    task = loop.create_task(
        send_push_to_category(category, title, body, url, exclude_user_id)
    )
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)


def notify_users(user_ids, title: str, body: str, url: str = "/app",
                 exclude_user_id: int = None):
    """Notification nominative, sans bloquer la requête."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        print(f"⚠️  Push : aucune boucle d'exécution, « {title} » non envoyé")
        return
    task = loop.create_task(
        send_push_to_users(user_ids, title, body, url, exclude_user_id)
    )
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
