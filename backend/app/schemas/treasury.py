"""Schémas Pydantic — Trésorerie."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from app.models.treasury import TransactionType, TransactionCategory
from app.schemas.common import NaiveDateTime


class TransactionCreate(BaseModel):
    transaction_type: TransactionType
    category: TransactionCategory = TransactionCategory.OTHER
    amount: float
    description: Optional[str] = None
    supplier: Optional[str] = None
    date: Optional[NaiveDateTime] = None

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
    # Provenance : « sumup-api », « sumup-csv », ou vide si saisie à la main.
    source: Optional[str] = None
    created_by: int
    invoices: list[dict] = []
    created_at: datetime
    class Config:
        from_attributes = True


class SumUpSettings(BaseModel):
    """Réglages de la liaison SumUp.

    La clé d'API n'est jamais renvoyée à l'interface ; ``api_key_set`` dit
    seulement si elle est enregistrée.
    """
    merchant_code: str = ""
    lookback_days: int = 90
    enabled: bool = False
    api_key_set: bool = False
    last_sync_at: Optional[datetime] = None


class SumUpSettingsUpdate(BaseModel):
    # Champ laissé vide = on conserve la clé déjà enregistrée.
    api_key: Optional[str] = None
    merchant_code: Optional[str] = None
    lookback_days: Optional[int] = None
    enabled: Optional[bool] = None


class ImportResult(BaseModel):
    """Bilan d'une synchronisation ou d'un import de relevé."""
    created: int = 0
    skipped: int = 0        # déjà importées lors d'un passage précédent
    income: int = 0
    expense: int = 0
    errors: list[str] = []
    detail: str = ""
