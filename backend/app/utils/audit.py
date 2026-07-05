"""Utilitaire d'audit — journalisation des actions."""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit import AuditLog


async def log_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    entity_type: str,
    entity_id: int = None,
    details: str = None,
    ip_address: str = None,
):
    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
        ip_address=ip_address,
    )
    db.add(entry)
