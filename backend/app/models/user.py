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
    # Historiquement nommée « email », cette colonne porte en réalité
    # l'**identifiant de connexion** (« paulin », « admin »). Elle est laissée
    # telle quelle : la renommer casserait les sessions et les imports CSV.
    email = Column(String(255), unique=True, nullable=False, index=True)
    # Adresse e-mail réelle de l'adhérent : sert à le joindre et à lui envoyer
    # un lien de réinitialisation de mot de passe.
    contact_email = Column(String(255), nullable=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True)
    # Rôle actif par défaut (parmi les rôles autorisés) ; NULL = tous ses rôles.
    default_role = Column(String(30), nullable=True)
    # Incrémenté à chaque changement de mot de passe : invalide immédiatement
    # tous les jetons déjà émis pour ce compte.
    token_version = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    roles = relationship("UserRole", cascade="all, delete-orphan", lazy="selectin")
    managed_hives = relationship("Hive", secondary="hive_managers", back_populates="managers", lazy="noload")
    visits = relationship("Visit", back_populates="author", lazy="noload")
    audit_logs = relationship("AuditLog", back_populates="user", lazy="noload")


class PasswordResetToken(Base):
    """Jeton à usage unique pour réinitialiser un mot de passe oublié.

    Seule l'empreinte du jeton est conservée : une fuite de la base ne permet
    donc pas de rejouer un lien encore valide. Le jeton en clair n'existe que
    dans l'e-mail envoyé à l'adhérent.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
