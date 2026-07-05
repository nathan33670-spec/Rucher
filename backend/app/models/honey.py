"""Modèles Miellée — suivi des récoltes, pots et ventes de miel."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class OwnershipFilter(str, enum.Enum):
    ASSOCIATIVE = "associative"
    PRIVATE = "private"


class HoneyCategory(Base):
    """Catégorie de miel (ex: Acacia, Toutes fleurs, Châtaignier…)."""
    __tablename__ = "honey_categories"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True)
    color = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    harvests = relationship("HoneyHarvest", back_populates="category", lazy="noload")


class HoneyHarvest(Base):
    """Enregistrement d'une récolte de miel."""
    __tablename__ = "honey_harvests"
    id = Column(Integer, primary_key=True, index=True)
    apiary_id = Column(Integer, ForeignKey("apiaries.id", ondelete="SET NULL"))
    hive_id = Column(Integer, ForeignKey("hives.id", ondelete="SET NULL"))
    category_id = Column(Integer, ForeignKey("honey_categories.id", ondelete="SET NULL"))
    ownership = Column(Enum(OwnershipFilter), default=OwnershipFilter.ASSOCIATIVE, nullable=False)
    harvest_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    quantity_kg = Column(Float, nullable=False)
    nb_frames = Column(Integer)
    nb_supers = Column(Integer)
    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    category = relationship("HoneyCategory", back_populates="harvests", lazy="selectin")
    apiary = relationship("Apiary", lazy="selectin")
    hive = relationship("Hive", lazy="selectin")
    jars = relationship("HoneyJar", back_populates="harvest", cascade="all, delete-orphan", lazy="selectin")


class JarSize(str, enum.Enum):
    JAR_1000 = "1000"
    JAR_500 = "500"
    JAR_250 = "250"
    JAR_125 = "125"


class HoneyJar(Base):
    """Stock de pots de miel issus d'une récolte."""
    __tablename__ = "honey_jars"
    id = Column(Integer, primary_key=True, index=True)
    harvest_id = Column(Integer, ForeignKey("honey_harvests.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(Integer, ForeignKey("honey_categories.id", ondelete="SET NULL"))
    ownership = Column(Enum(OwnershipFilter), default=OwnershipFilter.ASSOCIATIVE, nullable=False)
    jar_weight_g = Column(Integer, nullable=False)  # 1000, 500, 250, 125
    quantity = Column(Integer, default=0, nullable=False)  # stock actuel
    initial_quantity = Column(Integer, default=0, nullable=False)  # quantité mise en pot
    unit_price = Column(Float)  # prix de vente unitaire
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    harvest = relationship("HoneyHarvest", back_populates="jars")
    category = relationship("HoneyCategory", lazy="selectin")


class HoneySale(Base):
    """Vente de pots de miel (crée auto. une transaction en compta)."""
    __tablename__ = "honey_sales"
    id = Column(Integer, primary_key=True, index=True)
    jar_id = Column(Integer, ForeignKey("honey_jars.id", ondelete="CASCADE"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_amount = Column(Float, nullable=False)
    buyer = Column(String(300))  # nom de l'acheteur (optionnel)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"))
    sold_at = Column(DateTime, default=datetime.utcnow)
    sold_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    jar = relationship("HoneyJar", lazy="selectin")
