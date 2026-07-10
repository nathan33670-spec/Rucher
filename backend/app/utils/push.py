"""Notifications push web (VAPID + pywebpush).

- Les clés VAPID sont générées une fois et persistées dans app_settings.
- L'envoi est fait en tâche de fond (pywebpush est synchrone → asyncio.to_thread).
- Les abonnements expirés (404/410) sont supprimés automatiquement.
"""

import json
import base64
import asyncio

from sqlalchemy import select, delete
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
from pywebpush import webpush, WebPushException
from py_vapid import Vapid02

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


def _vapid_subject():
    return "mailto:" + (get_settings().first_admin_email or "admin@rucher.local")


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


async def _dispatch(subs, title, body, url):
    """Envoie le message à une liste d'abonnements (ouvre sa propre session)."""
    if not subs:
        return 0
    async with async_session() as db:
        priv, _pub = await get_or_create_vapid(db)
        await db.commit()
    payload = json.dumps({"title": title, "body": body, "url": url or "/app"})
    subject = _vapid_subject()
    vapid = Vapid02.from_pem(priv.encode())
    to_delete = []
    sent = 0
    for s in subs:
        try:
            await asyncio.to_thread(_send_one, s, payload, vapid, subject)
            sent += 1
        except WebPushException as e:
            code = getattr(getattr(e, "response", None), "status_code", None)
            if code in (404, 410):
                to_delete.append(s.id)
        except Exception:
            pass
    if to_delete:
        async with async_session() as db:
            await db.execute(delete(PushSubscription).where(PushSubscription.id.in_(to_delete)))
            await db.commit()
    return sent


async def send_push_to_category(category: str, title: str, body: str, url: str = "/app"):
    """Notifie tous les utilisateurs abonnés ayant activé cette catégorie."""
    if category not in CATEGORIES:
        return 0
    async with async_session() as db:
        field = getattr(NotificationPref, category)
        res = await db.execute(
            select(NotificationPref.user_id).where(
                NotificationPref.enabled.is_(True), field.is_(True)
            )
        )
        user_ids = list(res.scalars().all())
        if not user_ids:
            return 0
        res = await db.execute(
            select(PushSubscription).where(PushSubscription.user_id.in_(user_ids))
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


def notify(category: str, title: str, body: str, url: str = "/app"):
    """Déclenche l'envoi sans bloquer la requête (fire-and-forget)."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    task = loop.create_task(send_push_to_category(category, title, body, url))
    _bg_tasks.add(task)
    task.add_done_callback(_bg_tasks.discard)
