"""Authentification JWT et gestion des mots de passe."""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.database import get_db
from app.models.user import User, RoleEnum

ph = PasswordHasher()
security = HTTPBearer()
settings = get_settings()


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return ph.verify(hashed, plain)
    except VerifyMismatchError:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Dépendance : extrait l'utilisateur courant du token JWT."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token invalide")
    except (jwt.PyJWTError, Exception):
        raise HTTPException(status_code=401, detail="Token invalide")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Utilisateur introuvable ou inactif")
    return user


def get_user_roles(user: User) -> list[str]:
    """Retourne la liste des rôles d'un utilisateur."""
    return [r.role.value if hasattr(r.role, 'value') else r.role for r in user.roles]


def require_roles(*required: RoleEnum):
    """Dépendance : vérifie que l'utilisateur a au moins un des rôles requis."""
    async def checker(user: User = Depends(get_current_user)):
        user_roles = get_user_roles(user)
        if RoleEnum.ADMIN.value in user_roles:
            return user  # Admin peut tout faire
        for role in required:
            if role.value in user_roles:
                return user
        raise HTTPException(status_code=403, detail="Permissions insuffisantes")
    return checker
