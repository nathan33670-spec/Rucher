"""Schémas Pydantic — Visites."""

from pydantic import BaseModel, field_validator
from datetime import datetime, timedelta
from typing import Optional
from app.schemas.common import NaiveDateTime, NonEmptyStr


def _refuse_le_futur(v: Optional[datetime]) -> Optional[datetime]:
    """Une visite ne se fait pas demain.

    On tolère la fin de la journée en cours : le téléphone d'un adhérent peut
    être en avance de quelques heures sur le serveur, et refuser une visite
    du jour pour cela serait incompréhensible.
    """
    if v is None:
        return v
    limite = datetime.utcnow().replace(hour=23, minute=59, second=59) + timedelta(days=1)
    if v > limite:
        raise ValueError("La date de visite ne peut pas être dans le futur.")
    return v


class VisitCreate(BaseModel):
    hive_id: int
    # Date à laquelle la visite a eu lieu. Absente, c'est l'instant de la
    # saisie — le cas courant. Renseignée, elle permet de consigner après
    # coup une visite faite la veille au rucher, sans réseau ni téléphone.
    visited_at: Optional[NaiveDateTime] = None

    _pas_de_futur = field_validator("visited_at")(_refuse_le_futur)
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
    # La date de visite se corrige : on se trompe de jour en saisissant
    # plusieurs visites d'affilée, et rien ne permettait de le rattraper.
    # La date de saisie, elle, n'est jamais modifiable : c'est la trace de
    # quand l'information est entrée dans l'application.
    visited_at: Optional[NaiveDateTime] = None
    queen_seen: Optional[bool] = None

    _pas_de_futur = field_validator("visited_at")(_refuse_le_futur)
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
    hive_number: Optional[str] = None
    class Config:
        from_attributes = True
