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
    # Rapprochement bancaire : renseigné dès que l'écriture est pointée.
    reconciled_at: Optional[datetime] = None
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


class ReconciliationOut(BaseModel):
    """État du rapprochement d'un mois."""
    year: int
    month: int
    label: str                       # « septembre 2026 »
    validated: bool = False
    validated_at: Optional[datetime] = None
    validated_by_name: Optional[str] = None
    # Solde du relevé bancaire, saisi par le trésorier.
    statement_balance: Optional[float] = None
    notes: Optional[str] = None
    # Soldes calculés sur le mois.
    opening_balance: float = 0.0     # solde pointé des mois précédents
    reconciled_total: float = 0.0    # somme des écritures pointées du mois
    reconciled_balance: float = 0.0  # ouverture + pointé : ce que la banque devrait dire
    pending_total: float = 0.0       # écritures du mois non encore pointées
    difference: Optional[float] = None   # solde relevé − solde pointé
    counts: dict = {}                # {"total", "reconciled", "pending"}
    transactions: list[TransactionOut] = []


class ReconciliationMonth(BaseModel):
    """Ligne du suivi mensuel : sait-on où en est chaque mois ?"""
    year: int
    month: int
    label: str
    validated: bool = False
    validated_at: Optional[datetime] = None
    total: int = 0
    reconciled: int = 0
    pending: int = 0


class ReconciliationUpdate(BaseModel):
    statement_balance: Optional[float] = None
    notes: Optional[str] = None


class ReconciliationToggle(BaseModel):
    """Pointer ou dépointer des écritures d'un coup."""
    transaction_ids: list[int]
    reconciled: bool = True
