"""Routes — Récapitulatif hebdomadaire par e-mail."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, RoleEnum
from app.utils.auth import require_roles
from app.utils.audit import log_action
from app.utils import digest as digest_mod
from app.utils.mailer import send_mail, mail_enabled, recipients, MailNotConfigured
from app.routers.settings import load_mail

router = APIRouter(prefix="/api/reports", tags=["reports"])


def _window(days: int) -> tuple[datetime, datetime]:
    until = datetime.utcnow()
    return until - timedelta(days=days), until


@router.get("/weekly/status")
async def weekly_status(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Indique si l'envoi est configuré (diagnostic pour l'administrateur)."""
    cfg = await load_mail(db)
    return {
        "mail_configured": mail_enabled(cfg),
        "smtp_host": cfg.get("smtp_host") or None,
        "recipients": recipients(cfg),
        "enabled": bool(cfg.get("digest_enabled", True)),
        "weekday": int(cfg.get("digest_weekday") or 0),
        "hour": int(cfg.get("digest_hour") or 8),
        "source": cfg.get("source", "env"),
    }


@router.get("/weekly/preview", response_class=HTMLResponse)
async def weekly_preview(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Aperçu du récapitulatif, sans rien envoyer."""
    since, until = _window(days)
    data = await digest_mod.collect(db, since, until)
    cfg = await load_mail(db)
    _, html, _ = digest_mod.render(data, cfg.get("app_base_url") or "")
    return HTMLResponse(html)


@router.post("/weekly/send")
async def weekly_send(
    days: int = Query(7, ge=1, le=90),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Envoie immédiatement le récapitulatif (test ou rattrapage)."""
    since, until = _window(days)
    data = await digest_mod.collect(db, since, until)
    cfg = await load_mail(db)
    subject, html, text = digest_mod.render(data, cfg.get("app_base_url") or "")
    try:
        sent_to = await send_mail(subject, html, text, cfg=cfg)
    except MailNotConfigured as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Échec de l'envoi : {e}")
    await log_action(db, user.id, "send", "weekly_digest", details=f"{len(sent_to)} destinataire(s)")
    return {"detail": f"Récapitulatif envoyé à {len(sent_to)} destinataire(s)", "recipients": sent_to}
