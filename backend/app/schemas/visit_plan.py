"""Schémas Pydantic — Jours de visite planifiés."""

from pydantic import BaseModel
from datetime import date
from typing import Optional


class VisitPlanCreate(BaseModel):
    plan_date: date
    note: Optional[str] = None


class VisitPlanOut(BaseModel):
    id: int
    plan_date: date
    note: Optional[str] = None
    class Config:
        from_attributes = True
