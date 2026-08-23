"""Planificateur interne — envoi automatique du récapitulatif hebdomadaire.

Une tâche asyncio se réveille toutes les 15 minutes et vérifie si le créneau
d'envoi est atteint. Un marqueur en base (`app_settings`) garantit qu'un
récapitulatif n'est envoyé qu'une seule fois par semaine, même si le
conteneur redémarre plusieurs fois dans la journée.
"""

import asyncio
from datetime import datetime, timedelta

from app.routers.settings import load_mail
from app.database import async_session
from app.models.notification import AppSetting
from app.utils import digest as digest_mod
from app.utils.mailer import send_mail, mail_enabled, recipients

CHECK_INTERVAL = 900          # 15 minutes
MARKER_KEY = "weekly_digest_last_sent"   # valeur : identifiant de semaine ISO


def _week_id(now: datetime) -> str:
    y, w, _ = now.isocalendar()
    return f"{y}-W{w:02d}"


async def _already_sent(session, week: str) -> bool:
    row = await session.get(AppSetting, MARKER_KEY)
    return bool(row and row.value == week)


async def _mark_sent(session, week: str) -> None:
    row = await session.get(AppSetting, MARKER_KEY)
    if row:
        row.value = week
    else:
        session.add(AppSetting(key=MARKER_KEY, value=week))
    await session.commit()


async def _run_once() -> None:
    # La configuration réglée dans l'application prime sur le .env.
    async with async_session() as session:
        cfg = await load_mail(session)

    if not cfg.get("digest_enabled", True) or not mail_enabled(cfg) or not recipients(cfg):
        return

    now = datetime.now()
    # Créneau : le bon jour, à partir de l'heure prévue.
    if now.weekday() != int(cfg.get("digest_weekday") or 0) or now.hour < int(cfg.get("digest_hour") or 8):
        return

    week = _week_id(now)
    async with async_session() as session:
        if await _already_sent(session, week):
            return
        # Le marqueur est posé AVANT l'envoi : en cas d'échec SMTP répété, on
        # ne veut pas boucler et inonder le serveur de messages.
        await _mark_sent(session, week)

        until = datetime.utcnow()
        since = until - timedelta(days=7)
        data = await digest_mod.collect(session, since, until)
        subject, html, text = digest_mod.render(data, cfg.get("app_base_url") or "")

    try:
        sent = await send_mail(subject, html, text, cfg=cfg)
        print(f"✅ Récapitulatif hebdomadaire envoyé à {len(sent)} destinataire(s)")
    except Exception as e:
        print(f"⚠️  Envoi du récapitulatif hebdomadaire échoué : {e}")


async def weekly_digest_loop() -> None:
    """Boucle de fond ; ne doit jamais interrompre l'application."""
    # Laisse le temps à l'application de finir son démarrage.
    await asyncio.sleep(60)
    while True:
        try:
            await _run_once()
        except asyncio.CancelledError:
            raise
        except Exception as e:  # pragma: no cover
            print(f"⚠️  Planificateur du récapitulatif : {e}")
        await asyncio.sleep(CHECK_INTERVAL)
