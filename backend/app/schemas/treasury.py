"""Schémas Pydantic — Trésorerie."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.treasury import TransactionType, TransactionCategory


class TransactionCreate(BaseModel):
    transaction_type: TransactionType
    category: TransactionCategory = TransactionCategory.OTHER
    amount: float
    description: Optional[str] = None
    supplier: Optional[str] = None
    date: Optional[datetime] = None

class TransactionUpdate(BaseModel):
    transaction_type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    supplier: Optional[str] = None

class TransactionOut(BaseModel):
    id: int
    transaction_type: str
    category: str
    amount: float
    description: Optional[str] = None
    supplier: Optional[str] = None
    date: datetime
    created_by: int
    invoices: list[dict] = []
    created_at: datetime
    class Config:
        from_attributes = True
