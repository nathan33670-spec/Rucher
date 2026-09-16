"""Modèles Trésorerie."""

import enum
from datetime import datetime
from sqlalchemy import (Column, Integer, String, Float, DateTime, ForeignKey,
                        Text, Enum, Boolean, UniqueConstraint)
from sqlalchemy.orm import relationship
from app.database import Base


class TransactionType(str, enum.Enum):
    INCOME = "income"
    EXPENSE = "expense"


class TransactionCategory(str, enum.Enum):
    MATERIAL = "material"
    TREATMENT = "treatment"
    HONEY_SALE = "honey_sale"
    MEMBERSHIP = "membership"
    OTHER = "other"


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    category = Column(Enum(TransactionCategory), default=TransactionCategory.OTHER)
    amount = Column(Float, nullable=False)
    description = Column(Text)
    supplier = Column(String(300))  # fournisseur (optionnel)
    date = Column(DateTime, default=datetime.utcnow)
    # Provenance d'une écriture importée : « sumup-api », « sumup-csv », ou
    # vide pour une saisie à la main.
    source = Column(String(50), nullable=True)
    # Référence de l'opération chez SumUp. C'est elle qui rend les imports
    # rejouables : réimporter le même relevé ne recrée rien.
    external_ref = Column(String(255), nullable=True, index=True)
    # Rapprochement bancaire : une écriture « pointée » a été retrouvée sur le
    # relevé. Le lien vers le rapprochement permet de figer un mois validé.
    reconciled_at = Column(DateTime, nullable=True)
    reconciliation_id = Column(Integer, ForeignKey("bank_reconciliations.id",
                                                   ondelete="SET NULL"),
                               nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    invoices = relationship("Invoice", back_populates="transaction", cascade="all, delete-orphan", lazy="selectin")


class Invoice(Base):
    __tablename__ = "invoices"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_path = Column(String(500), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    transaction = relationship("Transaction", back_populates="invoices")


class BankReconciliation(Base):
    """Rapprochement bancaire d'un mois.

    Rapprocher, c'est confronter ce que dit l'association à ce que dit la
    banque : chaque écriture pointée a été retrouvée sur le relevé, et le
    solde obtenu doit tomber sur celui du relevé. Tant qu'un écart subsiste,
    il manque une écriture d'un côté ou de l'autre — c'est précisément ce que
    le rapprochement sert à débusquer.

    Un mois est « validé » quand le trésorier atteste que tout concorde. Il
    est alors figé : les écritures qu'il contient ne se dépointent plus sans
    rouvrir le mois, faute de quoi un exercice clos pourrait changer dans le
    dos de tout le monde.
    """
    __tablename__ = "bank_reconciliations"
    __table_args__ = (UniqueConstraint("year", "month", name="uq_reconciliation_periode"),)

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False, index=True)
    month = Column(Integer, nullable=False, index=True)
    # Solde du relevé bancaire à la fin du mois, saisi par le trésorier.
    statement_balance = Column(Float, nullable=True)
    # Solde des écritures pointées, figé à la validation : recalculé plus tard,
    # il changerait au gré des écritures ajoutées après coup.
    reconciled_balance = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    validated = Column(Boolean, default=False, nullable=False)
    validated_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
