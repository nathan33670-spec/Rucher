"""Schémas Pydantic — Miellée, pots et ventes."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class HoneyCategoryCreate(BaseModel):
    name: str
    color: Optional[str] = None
    description: Optional[str] = None

class HoneyCategoryOut(BaseModel):
    id: int
    name: str
    color: Optional[str] = None
    description: Optional[str] = None
    class Config:
        from_attributes = True

class HoneyHarvestCreate(BaseModel):
    apiary_id: Optional[int] = None
    hive_id: Optional[int] = None
    category_id: Optional[int] = None
    ownership: str = "associative"
    harvest_date: Optional[datetime] = None
    quantity_kg: float
    nb_frames: Optional[int] = None
    nb_supers: Optional[int] = None
    notes: Optional[str] = None

class HoneyHarvestUpdate(BaseModel):
    apiary_id: Optional[int] = None
    hive_id: Optional[int] = None
    category_id: Optional[int] = None
    ownership: Optional[str] = None
    harvest_date: Optional[datetime] = None
    quantity_kg: Optional[float] = None
    nb_frames: Optional[int] = None
    nb_supers: Optional[int] = None
    notes: Optional[str] = None

class HoneyHarvestOut(BaseModel):
    id: int
    apiary_id: Optional[int] = None
    hive_id: Optional[int] = None
    category_id: Optional[int] = None
    ownership: str = "associative"
    harvest_date: datetime
    quantity_kg: float
    nb_frames: Optional[int] = None
    nb_supers: Optional[int] = None
    notes: Optional[str] = None
    created_by: int
    created_at: datetime
    category_name: Optional[str] = None
    apiary_name: Optional[str] = None
    hive_name: Optional[str] = None
    jars: list[dict] = []
    class Config:
        from_attributes = True

# ─── Pots ─────────────────────────────

class JarCreate(BaseModel):
    harvest_id: int
    category_id: Optional[int] = None
    ownership: str = "associative"
    jar_weight_g: int  # 1000, 500, 250, 125
    quantity: int
    unit_price: Optional[float] = None

class JarUpdate(BaseModel):
    quantity: Optional[int] = None
    unit_price: Optional[float] = None

class JarOut(BaseModel):
    id: int
    harvest_id: int
    category_id: Optional[int] = None
    ownership: str = "associative"
    jar_weight_g: int
    quantity: int
    initial_quantity: int
    unit_price: Optional[float] = None
    category_name: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

# ─── Ventes ───────────────────────────

class SaleCreate(BaseModel):
    jar_id: int
    quantity: int
    unit_price: Optional[float] = None  # si non fourni, prend le prix du pot
    buyer: Optional[str] = None

class SaleOut(BaseModel):
    id: int
    jar_id: int
    quantity: int
    unit_price: float
    total_amount: float
    buyer: Optional[str] = None
    transaction_id: Optional[int] = None
    sold_at: datetime
    sold_by: int
    jar_weight_g: Optional[int] = None
    category_name: Optional[str] = None
    ownership: Optional[str] = None
    class Config:
        from_attributes = True
