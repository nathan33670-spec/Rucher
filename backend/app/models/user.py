"""Modèle Utilisateur et Rôles."""

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class RoleEnum(str, enum.Enum):
    ADMIN = "admin"
    TREASURER = "treasurer"
    YARD_MANAGER = "yard_manager"
    USER = "user"
    READONLY = "readonly"


class UserRole(Base):
    __tablename__ = "user_roles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = relationship("UserRole", cascade="all, delete-orphan", lazy="selectin")
    managed_hives = relationship("Hive", secondary="hive_managers", back_populates="managers", lazy="noload")
    visits = relationship("Visit", back_populates="author", lazy="noload")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="noload")
