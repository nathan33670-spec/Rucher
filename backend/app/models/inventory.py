"""Modèles Inventaire."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class MovementType(str, enum.Enum):
    IN = "in"
    OUT = "out"


class InventoryItem(Base):
    __tablename__ = "inventory_items"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category = Column(String(100))
    description = Column(Text)
    location = Column(String(200))
    quantity = Column(Integer, default=0)
    unit = Column(String(50), default="unité")
    alert_threshold = Column(Integer)
    qr_code = Column(String(500))
    unit_price = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    movements = relationship("InventoryMovement", back_populates="item", cascade="all, delete-orphan", lazy="selectin")


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"
    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("inventory_items.id", ondelete="CASCADE"), nullable=False)
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)
    reason = Column(String(500))
    hive_id = Column(Integer, ForeignKey("hives.id"))
    transaction_id = Column(Integer, ForeignKey("transactions.id"))
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)
    item = relationship("InventoryItem", back_populates="movements")
