"""Routes — Visites de ruches."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.database import get_db
from app.models.visit import Visit
from app.models.apiary import Hive
from app.models.user import User, RoleEnum
from app.schemas.visit import VisitCreate, VisitUpdate, VisitOut
from app.utils.auth import get_current_user, get_user_roles
from app.utils.audit import log_action
from app.utils.push import notify


def _hive_label(hive: Hive) -> str:
    if not hive:
        return "Ruche"
    return hive.name or hive.napi_number or f"Ruche #{hive.id}"

router = APIRouter(prefix="/api/visits", tags=["visits"])


@router.get("/", response_model=list[VisitOut])
async def list_visits(
    hive_id: int = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    q = select(Visit).order_by(desc(Visit.visited_at)).limit(limit)
    if hive_id:
        q = q.where(Visit.hive_id == hive_id)
    result = await db.execute(q)
    visits = result.scalars().all()
    out = []
    for v in visits:
        author = await db.get(User, v.author_id)
        hive = await db.get(Hive, v.hive_id)
        out.append(_visit_out(v, author, hive))
    return out


@router.get("/stats")
async def visit_stats(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Comptages pour le tableau de bord : visites du mois en cours et total."""
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)
    month = await db.scalar(
        select(func.count()).select_from(Visit).where(Visit.visited_at >= month_start)
    )
    total = await db.scalar(select(func.count()).select_from(Visit))
    return {"month": month or 0, "total": total or 0}


@router.post("/", response_model=VisitOut, status_code=201)
async def create_visit(
    body: VisitCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Vérifier droits sur la ruche
    hive = await db.get(Hive, body.hive_id)
    if not hive:
        raise HTTPException(404, "Ruche introuvable")
    _check_hive_access(user, hive)

    visited = body.visited_at or datetime.utcnow()
    if hasattr(visited, 'tzinfo') and visited.tzinfo is not None:
        visited = visited.replace(tzinfo=None)

    visit = Visit(
        **body.model_dump(exclude_unset=True, exclude={"visited_at"}),
        author_id=user.id,
        visited_at=visited,
    )
    db.add(visit)
    await db.flush()
    await log_action(db, user.id, "create", "visit", visit.id)

    # Notifications push (aux abonnés ayant activé la catégorie)
    label = _hive_label(hive)
    notify("visits", "🐝 Nouvelle visite",
           f"{user.first_name} a saisi une visite — {label}", "/app/visits")
    if visit.is_alert:
        notify("alerts", "⚠️ Alerte rucher",
               f"{label} : {visit.alert_message or 'à vérifier'}", "/app")

    return _visit_out(visit, user, hive)


@router.post("/batch", response_model=list[VisitOut], status_code=201)
async def sync_visits(
    visits: list[VisitCreate],
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Synchronisation batch des visites hors-ligne."""
    out = []
    for body in visits:
        hive = await db.get(Hive, body.hive_id)
        if not hive:
            continue
        bv = body.visited_at or datetime.utcnow()
        if hasattr(bv, 'tzinfo') and bv.tzinfo is not None:
            bv = bv.replace(tzinfo=None)
        visit = Visit(
            **body.model_dump(exclude_unset=True, exclude={"visited_at"}),
            author_id=user.id,
            visited_at=bv,
            synced=True,
        )
        db.add(visit)
        await db.flush()
        out.append(_visit_out(visit, user, hive))
    if out:
        notify("visits", "🐝 Visites synchronisées",
               f"{user.first_name} a synchronisé {len(out)} visite(s).", "/app/visits")
    return out


@router.put("/{visit_id}", response_model=VisitOut)
async def update_visit(
    visit_id: int,
    body: VisitUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    visit = await db.get(Visit, visit_id)
    if not visit:
        raise HTTPException(404, "Visite introuvable")

    hive = await db.get(Hive, visit.hive_id)
    _check_hive_access(user, hive)

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(visit, k, v)
    await log_action(db, user.id, "update", "visit", visit.id)
    author = await db.get(User, visit.author_id)
    return _visit_out(visit, author, hive)


@router.delete("/{visit_id}", status_code=204)
async def delete_visit(
    visit_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Seuls les admins peuvent supprimer une visite."""
    roles = get_user_roles(user)
    if RoleEnum.ADMIN.value not in roles:
        raise HTTPException(403, "Seuls les administrateurs peuvent supprimer des visites")
    visit = await db.get(Visit, visit_id)
    if not visit:
        raise HTTPException(404, "Visite introuvable")
    await db.delete(visit)
    await log_action(db, user.id, "delete", "visit", visit_id)


def _check_hive_access(user: User, hive: Hive):
    """Vérifie que l'utilisateur peut intervenir sur cette ruche."""
    roles = get_user_roles(user)
    if RoleEnum.ADMIN.value in roles or RoleEnum.YARD_MANAGER.value in roles:
        return
    if any(m.id == user.id for m in hive.managers):
        return
    raise HTTPException(403, "Vous n'avez pas accès à cette ruche")


def _visit_out(v: Visit, author: User = None, hive: Hive = None) -> VisitOut:
    return VisitOut(
        id=v.id, hive_id=v.hive_id, author_id=v.author_id,
        visited_at=v.visited_at, queen_seen=v.queen_seen,
        brood_score=v.brood_score, reserves_score=v.reserves_score,
        supers_count=v.supers_count, supers_delta=v.supers_delta,
        feeding=v.feeding,
        comment=v.comment, is_alert=v.is_alert,
        alert_message=v.alert_message, honey_harvest_kg=v.honey_harvest_kg,
        is_live_mode=v.is_live_mode, synced=v.synced,
        created_at=v.created_at,
        author_name=f"{author.first_name} {author.last_name}" if author else None,
        hive_name=_hive_label(hive) if hive else None,
    )
