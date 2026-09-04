"""Schémas Pydantic — Utilisateurs."""

from pydantic import BaseModel, Field, AliasChoices
from datetime import datetime
from typing import Optional
from app.models.user import RoleEnum
from app.schemas.common import NonEmptyStr


class UserCreate(BaseModel):
    email: NonEmptyStr
    password: str
    first_name: NonEmptyStr
    last_name: NonEmptyStr
    phone: Optional[str] = None
    roles: list[RoleEnum] = [RoleEnum.USER]


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    roles: Optional[list[RoleEnum]] = None


class UserOut(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    is_active: bool
    roles: list[str] = []            # rôles autorisés (attribués par l'admin)
    selectable_roles: list[str] = []   # rôles utilisables (attribués + impliqués)
    active_role: Optional[str] = None  # rôle actif courant (None = tous)
    default_role: Optional[str] = None # rôle actif par défaut
    created_at: datetime
    class Config:
        from_attributes = True


class SwitchRoleIn(BaseModel):
    role: Optional[str] = None   # None = utiliser tous ses rôles


class PasswordReset(BaseModel):
    new_password: str


class SelfPasswordChange(BaseModel):
    """Changement de mot de passe par l'utilisateur lui-même."""
    current_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    # Connexion par nom d'utilisateur (identifiant), plus par e-mail.
    # Le champ JSON « email » reste accepté (compatibilité ascendante).
    username: str = Field(validation_alias=AliasChoices("username", "email"))
    password: str
    # « Rester connecté » : demande un jeton quasi-permanent (10 ans).
    remember: bool = False
