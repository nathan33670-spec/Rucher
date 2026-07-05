"""Modèles Rucher (Apiary) et Ruche (Hive)."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Table, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class OwnershipType(str, enum.Enum):
    ASSOCIATIVE = "associative"
    PRIVATE = "private"


hive_managers = Table(
    "hive_managers", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("hive_id", Integer, ForeignKey("hives.id", ondelete="CASCADE"), primary_key=True),
)


class Apiary(Base):
    __tablename__ = "apiaries"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    address = Column(String(500))
    latitude = Column(Float)
    longitude = Column(Float)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    hives = relationship("Hive", back_populates="apiary", cascade="all, delete-orphan", lazy="selectin")


class Hive(Base):
    __tablename__ = "hives"
    id = Column(Integer, primary_key=True, index=True)
    apiary_id = Column(Integer, ForeignKey("apiaries.id", ondelete="CASCADE"), nullable=False)
    napi_number = Column(String(50), index=True)
    name = Column(String(200))
    ownership = Column(Enum(OwnershipType), default=OwnershipType.ASSOCIATIVE, nullable=False)
    position_x = Column(Float)
    position_y = Column(Float)
    status = Column(String(50), default="active")
    notes = Column(Text)
    photo_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    apiary = relationship("Apiary", back_populates="hives")
    managers = relationship("User", secondary=hive_managers, back_populates="managed_hives", lazy="selectin")
    visits = relationship("Visit", back_populates="hive", cascade="all, delete-orphan", lazy="noload")
    sanitary_records = relationship("SanitaryRecord", back_populates="hive", cascade="all, delete-orphan", lazy="noload")
