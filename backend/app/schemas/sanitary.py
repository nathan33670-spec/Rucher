"""Schémas Pydantic — Sanitaire."""

from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional


class SanitaryCreate(BaseModel):
    hive_ids: list[int] = []       # plusieurs ruches possibles
    hive_id: Optional[int] = None  # compatibilité ancienne
    record_type: str = "treatment"  # "treatment" ou "varroa_count"
    treatment_type: Optional[str] = None
    product: Optional[str] = None
    dosage: Optional[str] = None
    application_date: date
    end_date: Optional[date] = None
    varroa_count: Optional[int] = None
    notes: Optional[str] = None

class SanitaryUpdate(BaseModel):
    treatment_type: Optional[str] = None
    product: Optional[str] = None
    dosage: Optional[str] = None
    end_date: Optional[date] = None
    varroa_count: Optional[int] = None
    notes: Optional[str] = None

class SanitaryOut(BaseModel):
    id: int
    hive_id: int
    record_type: str = "treatment"
    treatment_type: Optional[str] = None
    product: Optional[str] = None
    dosage: Optional[str] = None
    application_date: date
    end_date: Optional[date] = None
    varroa_count: Optional[int] = None
    notes: Optional[str] = None
    performed_by: int
    created_at: datetime
    hive_name: Optional[str] = None
    class Config:
        from_attributes = True
