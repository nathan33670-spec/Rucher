"""Annonce d'une nouvelle version aux adhérents.

Au démarrage, si la version du code diffère de celle déjà annoncée, chacun
reçoit la note de version dans sa boîte de réception (et en notification push
s'il y est abonné). Le repère est stocké en base : redémarrer le conteneur ne
renvoie donc pas l'annonce.
"""

import json

from sqlalchemy import select

from app.database import async_session
from app.models.notification import AppSetting
from app.models.user import User
from app.releases import CURRENT_VERSION, latest
from app.utils.push import store_inbox, send_push_to_users

RELEASE_KEY = "last_release_notified"


def _summary(release: dict, max_items: int = 3) -> str:
    items = release.get("highlights") or []
    text = " · ".join(items[:max_items])
    if len(items) > max_items:
        text += f" (+{len(items) - max_items} autre(s))"
    return text or release.get("title", "")


async def announce_new_release() -> bool:
    """Annonce la version courante si elle ne l'a pas déjà été.

    Renvoie True si une annonce a été envoyée.
    """
    release = latest()
    async with async_session() as db:
        row = await db.get(AppSetting, RELEASE_KEY)
        if row and row.value == CURRENT_VERSION:
            return False

        first_run = row is None
        if row:
            row.value = CURRENT_VERSION
        else:
            db.add(AppSetting(key=RELEASE_KEY, value=CURRENT_VERSION))

        # Première installation : on enregistre la version sans inonder les
        # comptes d'une annonce pour un historique qu'ils n'ont pas vécu.
        if first_run:
            await db.commit()
            print(f"ℹ️  Version {CURRENT_VERSION} enregistrée (pas d'annonce au premier démarrage)")
            return False

        res = await db.execute(select(User.id).where(User.is_active.is_(True)))
        user_ids = list(res.scalars().all())
        if not user_ids:
            await db.commit()
            return False

        title = f"🐝 Rucher Manager {CURRENT_VERSION} — {release['title']}"
        body = _summary(release)
        await store_inbox(db, user_ids, "release", title, body, "/docs/versions")
        await db.commit()

    # Déjà archivé ci-dessus : on ne demande ici que l'envoi push.
    await send_push_to_users(user_ids, title, body, "/docs/versions",
                             category="release", store=False)
    print(f"✅ Version {CURRENT_VERSION} annoncée à {len(user_ids)} adhérent(s)")
    return True
