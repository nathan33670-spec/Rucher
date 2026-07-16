"""Schémas Pydantic — Utilisateurs."""

from pydantic import BaseModel, Field, AliasChoices
from datetime import datetime
from typing import Optional
from app.models.user import RoleEnum


class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
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
    roles: list[str] = []
    created_at: datetime
    class Config:
        from_attributes = True


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
