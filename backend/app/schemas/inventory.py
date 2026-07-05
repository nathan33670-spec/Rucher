"""Schémas Pydantic — Inventaire."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.inventory import MovementType


class ItemCreate(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    quantity: int = 0
    unit: str = "unité"
    alert_threshold: Optional[int] = None
    unit_price: Optional[float] = None

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    alert_threshold: Optional[int] = None
    unit_price: Optional[float] = None

class ItemMove(BaseModel):
    """Déplacement d'un article vers un emplacement.
    `quantity` à None ou >= au stock = déplacement total ; sinon scission partielle."""
    new_location: Optional[str] = None
    quantity: Optional[int] = None

class ItemOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    location: Optional[str] = None
    quantity: int
    unit: str
    alert_threshold: Optional[int] = None
    unit_price: Optional[float] = None
    qr_code: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True

class MovementCreate(BaseModel):
    item_id: int
    movement_type: MovementType
    quantity: int
    reason: Optional[str] = None
    hive_id: Optional[int] = None
    transaction_id: Optional[int] = None

class MovementOut(BaseModel):
    id: int
    item_id: int
    movement_type: str
    quantity: int
    reason: Optional[str] = None
    performed_by: int
    performed_at: datetime
    class Config:
        from_attributes = True
