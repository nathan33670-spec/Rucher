"""Schémas Pydantic — Visites."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.schemas.common import NaiveDateTime, NonEmptyStr


class VisitCreate(BaseModel):
    hive_id: int
    visited_at: Optional[NaiveDateTime] = None
    queen_seen: Optional[bool] = None
    brood_score: Optional[int] = None       # null = N/A (corps non ouvert)
    reserves_score: Optional[int] = None    # null = N/A
    supers_count: Optional[int] = None
    frames_count: Optional[int] = None
    supers_delta: int = 0
    feeding: Optional[str] = None
    comment: Optional[str] = None
    is_alert: bool = False
    alert_message: Optional[str] = None
    honey_harvest_kg: Optional[float] = None
    pollen_harvest_kg: Optional[float] = None
    treatment_type: Optional[str] = None
    treatment_product: Optional[str] = None
    is_live_mode: bool = False

class HiveAlertIn(BaseModel):
    """Signalement d'un problème sur une ruche (menu « Signaler un problème »)."""
    hive_id: int
    message: NonEmptyStr


class VisitUpdate(BaseModel):
    queen_seen: Optional[bool] = None
    brood_score: Optional[int] = None
    reserves_score: Optional[int] = None
    supers_count: Optional[int] = None
    frames_count: Optional[int] = None
    supers_delta: Optional[int] = None
    feeding: Optional[str] = None
    comment: Optional[str] = None
    is_alert: Optional[bool] = None
    alert_message: Optional[str] = None
    honey_harvest_kg: Optional[float] = None
    pollen_harvest_kg: Optional[float] = None
    treatment_type: Optional[str] = None
    treatment_product: Optional[str] = None

class VisitOut(BaseModel):
    id: int
    hive_id: int
    author_id: int
    visited_at: datetime
    queen_seen: Optional[bool] = None
    brood_score: Optional[int] = None
    reserves_score: Optional[int] = None
    supers_count: Optional[int] = None
    frames_count: Optional[int] = None
    supers_delta: int
    feeding: Optional[str] = None
    comment: Optional[str] = None
    is_alert: bool
    alert_message: Optional[str] = None
    honey_harvest_kg: Optional[float] = None
    pollen_harvest_kg: Optional[float] = None
    treatment_type: Optional[str] = None
    treatment_product: Optional[str] = None
    is_live_mode: bool
    synced: bool
    created_at: datetime
    author_name: Optional[str] = None
    hive_name: Optional[str] = None
    class Config:
        from_attributes = True
