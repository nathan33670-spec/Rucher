"""Routes — Visites de ruches."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.visit import Visit
from app.models.apiary import Hive, Apiary
from app.models.sanitary import SanitaryRecord
from app.models.user import User, RoleEnum
from app.schemas.visit import VisitCreate, VisitUpdate, VisitOut, HiveAlertIn
from app.utils.auth import get_current_user, get_user_roles
from app.utils.audit import log_action
from app.utils.push import notify, notify_users


def _hive_label(hive: Hive) -> str:
    if not hive:
        return "Ruche"
    return hive.name or hive.napi_number or f"Ruche #{hive.id}"


def _record_treatment(db: AsyncSession, visit: Visit, user: User) -> None:
    """Reporte le traitement saisi sur le terrain dans le registre sanitaire.

    Le traitement reste stocké sur la visite (historique de la ruche) mais il
    doit aussi apparaître dans le suivi sanitaire, qui fait office de registre
    réglementaire. Appelé uniquement à la création d'une visite.
    """
    if not visit.treatment_type:
        return
    db.add(SanitaryRecord(
        hive_id=visit.hive_id,
        record_type="treatment",
        treatment_type=visit.treatment_type,
        product=visit.treatment_product,
        application_date=visit.visited_at.date(),
        notes="Saisi lors d'une visite de ruche",
        performed_by=user.id,
    ))

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


@router.get("/last")
async def last_visit_per_hive(
    hive_ids: str = Query(None, description="Identifiants séparés par des virgules"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Dernière visite de chaque ruche, indexée par ruche.

    Sert à pré-remplir la visite rapide : on repart des valeurs connues plutôt
    que de zéro. Un seul appel couvre toute la tournée, ce qui permet aussi de
    travailler hors connexion une fois la page chargée.
    """
    wanted = None
    if hive_ids:
        try:
            wanted = [int(x) for x in hive_ids.split(",") if x.strip()]
        except ValueError:
            raise HTTPException(400, "Liste de ruches invalide")
        if not wanted:
            return {}

    # Date de la dernière visite par ruche, puis la visite correspondante.
    sub = select(Visit.hive_id, func.max(Visit.visited_at).label("last_at"))
    if wanted:
        sub = sub.where(Visit.hive_id.in_(wanted))
    sub = sub.group_by(Visit.hive_id).subquery()

    result = await db.execute(
        select(Visit)
        .join(sub, (Visit.hive_id == sub.c.hive_id) & (Visit.visited_at == sub.c.last_at))
        .order_by(desc(Visit.id))
    )

    out: dict[str, dict] = {}
    authors: dict[int, User] = {}
    for v in result.scalars().all():
        # Deux visites à la même seconde : la plus récemment enregistrée gagne
        # (tri décroissant sur l'identifiant), on ne garde donc que la première.
        key = str(v.hive_id)
        if key in out:
            continue
        if v.author_id not in authors:
            authors[v.author_id] = await db.get(User, v.author_id)
        a = authors[v.author_id]
        out[key] = {
            "id": v.id,
            "visited_at": v.visited_at.isoformat(),
            "queen_seen": v.queen_seen,
            "brood_score": v.brood_score,
            "reserves_score": v.reserves_score,
            "supers_count": v.supers_count,
            "frames_count": v.frames_count,
            "feeding": v.feeding,
            "is_alert": v.is_alert,
            "author_name": (f"{a.first_name or ''} {a.last_name or ''}".strip()
                            if a else None),
        }
    return out


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
    _record_treatment(db, visit, user)

    # Notifications push (aux abonnés ayant activé la catégorie)
    label = _hive_label(hive)
    notify("visits", "🐝 Nouvelle visite",
           f"{user.first_name} a saisi une visite — {label}", "/app/visits",
           exclude_user_id=user.id)
    if visit.is_alert:
        notify("alerts", "⚠️ Alerte rucher",
               f"{label} : {visit.alert_message or 'à vérifier'}", "/app",
               exclude_user_id=user.id)

    return _visit_out(visit, user, hive)


@router.post("/alert", response_model=VisitOut, status_code=201)
async def report_hive_problem(
    body: HiveAlertIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Signale un problème sur une ruche et prévient ses responsables.

    Le signalement est enregistré comme une observation d'alerte : il apparaît
    donc dans l'historique de la ruche et dans les alertes du tableau de bord,
    au lieu de rester un message sans trace. Tout adhérent peut signaler —
    y compris sur une ruche dont il n'a pas la charge, puisque c'est justement
    aux responsables qu'il doit pouvoir donner l'alerte.
    """
    result = await db.execute(
        select(Hive).options(selectinload(Hive.managers)).where(Hive.id == body.hive_id)
    )
    hive = result.scalar_one_or_none()
    if not hive:
        raise HTTPException(404, "Ruche introuvable")

    message = body.message.strip()
    visit = Visit(
        hive_id=hive.id,
        author_id=user.id,
        visited_at=datetime.utcnow(),
        comment=message,
        is_alert=True,
        alert_message=message[:500],
    )
    db.add(visit)
    await db.flush()
    await log_action(db, user.id, "alert", "visit", visit.id, details=message[:200])

    label = _hive_label(hive)
    apiary = await db.get(Apiary, hive.apiary_id)
    where = f" ({apiary.name})" if apiary else ""
    who = f"{user.first_name} {user.last_name}".strip() or user.email
    title = f"⚠️ Problème signalé — {label}"
    text = f"{who}{where} : {message[:180]}"

    # Les responsables de la ruche sont prévenus nommément : ce sont eux qui
    # doivent intervenir. Les autres abonnés à la catégorie « alertes » le sont
    # aussi, mais jamais l'auteur du signalement.
    manager_ids = [m.id for m in hive.managers]
    if manager_ids:
        notify_users(manager_ids, title, text, "/app/visits", exclude_user_id=user.id)
    notify("alerts", title, text, "/app/visits", exclude_user_id=user.id)

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
        # Tracée comme une saisie directe : sans cela, les visites remontées
        # depuis le mode hors-ligne n'apparaissaient pas au journal.
        await log_action(db, user.id, "create", "visit", visit.id, details="sync hors-ligne")
        _record_treatment(db, visit, user)
        out.append(_visit_out(visit, user, hive))
    if out:
        notify("visits", "🐝 Visites synchronisées",
               f"{user.first_name} a synchronisé {len(out)} visite(s).", "/app/visits",
               exclude_user_id=user.id)
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
        supers_count=v.supers_count, frames_count=v.frames_count,
        supers_delta=v.supers_delta,
        feeding=v.feeding,
        comment=v.comment, is_alert=v.is_alert,
        alert_message=v.alert_message, honey_harvest_kg=v.honey_harvest_kg,
        pollen_harvest_kg=v.pollen_harvest_kg,
        treatment_type=v.treatment_type, treatment_product=v.treatment_product,
        is_live_mode=v.is_live_mode, synced=v.synced,
        created_at=v.created_at,
        author_name=(f"{author.first_name or ''} {author.last_name or ''}".strip()
                     if author else None),
        hive_name=_hive_label(hive) if hive else None,
    )
