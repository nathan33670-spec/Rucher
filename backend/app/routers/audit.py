"""Routes — Journal d'audit."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.models.audit import AuditLog
from app.models.user import User, RoleEnum
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/audit", tags=["audit"])


@router.get("/")
async def list_logs(
    limit: int = Query(50, le=500),
    entity_type: str = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit)
    if entity_type:
        q = q.where(AuditLog.entity_type == entity_type)
    result = await db.execute(q)
    logs = result.scalars().all()
    out = []
    for log in logs:
        author = await db.get(User, log.user_id) if log.user_id else None
        out.append({
            "id": log.id,
            "user_id": log.user_id,
            "user_name": f"{author.first_name} {author.last_name}" if author else None,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "details": log.details,
            "created_at": log.created_at.isoformat(),
        })
    return out
