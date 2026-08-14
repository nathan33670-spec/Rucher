"""Schémas Pydantic — Réglages de l'application."""

from pydantic import BaseModel, Field
from typing import Optional


class IdealCriteria(BaseModel):
    """Conditions d'un créneau « idéal » pour ouvrir les ruches."""
    hour_start: int = Field(10, ge=0, le=23)
    hour_end: int = Field(18, ge=0, le=23)
    temp_min: float = 15
    temp_max: float = 30
    rain_max: float = Field(30, ge=0, le=100)   # probabilité de pluie (%)
    wind_max: float = Field(25, ge=0)           # km/h
    min_hours: int = Field(2, ge=1, le=12)      # heures idéales requises dans la journée


class OkCriteria(BaseModel):
    """Conditions d'une journée « correcte » (à défaut d'idéale)."""
    temp_min: float = 12
    rain_max: float = Field(50, ge=0, le=100)
    wind_max: float = Field(35, ge=0)


class WeatherCriteria(BaseModel):
    ideal: IdealCriteria = IdealCriteria()
    ok: OkCriteria = OkCriteria()


class WeatherCriteriaUpdate(BaseModel):
    ideal: Optional[IdealCriteria] = None
    ok: Optional[OkCriteria] = None
