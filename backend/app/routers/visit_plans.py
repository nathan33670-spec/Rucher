"""Routes — Jours de visite planifiés (préférences par utilisateur, modifiables)."""

from datetime import date
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.visit_plan import VisitPlan
from app.models.user import User
from app.schemas.visit_plan import VisitPlanCreate, VisitPlanOut
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/visit-plans", tags=["visit-plans"])


@router.get("/", response_model=list[VisitPlanOut])
async def my_plans(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(VisitPlan).where(VisitPlan.user_id == user.id).order_by(VisitPlan.plan_date)
    )
    return list(result.scalars().all())


@router.post("/", response_model=VisitPlanOut, status_code=201)
async def add_or_update_plan(
    body: VisitPlanCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(VisitPlan).where(VisitPlan.user_id == user.id, VisitPlan.plan_date == body.plan_date)
    )
    plan = result.scalar_one_or_none()
    if plan:
        plan.note = body.note
    else:
        plan = VisitPlan(user_id=user.id, plan_date=body.plan_date, note=body.note)
        db.add(plan)
    await db.flush()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_date}")
async def remove_plan(
    plan_date: date,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(VisitPlan).where(VisitPlan.user_id == user.id, VisitPlan.plan_date == plan_date)
    )
    plan = result.scalar_one_or_none()
    if plan:
        await db.delete(plan)
    return {"detail": "supprimé"}
