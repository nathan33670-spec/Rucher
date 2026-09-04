"""Authentification JWT et gestion des mots de passe."""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends, HTTPException, Request, status
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


# Écritures tolérées pour un compte en lecture seule : elles ne concernent que
# son propre compte et son propre appareil, jamais les données de l'association.
READONLY_ALLOWED_PATHS = (
    "/api/users/me/password",
    "/api/users/me/default-role",
    "/api/users/switch-role",
    "/api/notifications/subscribe",
    "/api/notifications/unsubscribe",
    "/api/notifications/preferences",
    "/api/notifications/test",
    # Préférences météo personnelles : ne concernent que l'affichage de son
    # propre écran, jamais les données de l'association.
    "/api/settings/weather/mine",
)

SAFE_METHODS = ("GET", "HEAD", "OPTIONS")


async def get_current_user(
    request: Request,
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
    # Version de jeton : un changement de mot de passe incrémente le compteur
    # en base, ce qui périme instantanément les jetons émis auparavant.
    # Les jetons antérieurs à cette fonctionnalité n'ont pas la revendication ;
    # ils restent valables jusqu'au prochain changement de mot de passe.
    tv = payload.get("tv")
    if tv is not None and int(tv) != int(user.token_version or 0):
        raise HTTPException(
            status_code=401,
            detail="Session expirée (mot de passe modifié). Reconnectez-vous.",
        )

    # Rôle « actif » transporté par le jeton (commutation de rôle à la volée).
    user.active_role = payload.get("active_role")

    # Lecture seule : aucune écriture sur les données de l'association.
    if request.method not in SAFE_METHODS and _is_readonly(user):
        if request.url.path not in READONLY_ALLOWED_PATHS:
            raise HTTPException(
                status_code=403,
                detail="Votre compte est en lecture seule : modification impossible.",
            )

    return user


def _is_readonly(user: User) -> bool:
    """Vrai si les droits EFFECTIFS se limitent au rôle « lecture seule ».

    Un compte cumulant « readonly » et un autre rôle garde les droits de
    l'autre rôle — sauf s'il a explicitement sélectionné « lecture seule »
    comme rôle actif, auquel cas la restriction s'applique.
    """
    roles = get_user_roles(user)
    return bool(roles) and all(r == RoleEnum.READONLY.value for r in roles)


def get_authorized_roles(user: User) -> list[str]:
    """Tous les rôles réellement attribués à l'utilisateur (par l'admin)."""
    return [r.role.value if hasattr(r.role, 'value') else r.role for r in user.roles]


# Hiérarchie des rôles : un rôle « contient » les rôles moins puissants.
# Elle ne sert qu'à DESCENDRE en droits — se restreindre volontairement est
# toujours sûr. On ne remonte jamais au-dessus des rôles attribués par l'admin.
ROLE_IMPLIES: dict[str, tuple[str, ...]] = {
    RoleEnum.ADMIN.value: (
        RoleEnum.TREASURER.value,
        RoleEnum.YARD_MANAGER.value,
        RoleEnum.USER.value,
        RoleEnum.READONLY.value,
    ),
    RoleEnum.TREASURER.value: (RoleEnum.USER.value, RoleEnum.READONLY.value),
    RoleEnum.YARD_MANAGER.value: (RoleEnum.USER.value, RoleEnum.READONLY.value),
    RoleEnum.USER.value: (RoleEnum.READONLY.value,),
    RoleEnum.READONLY.value: (),
}

# Ordre d'affichage, du plus étendu au plus restreint.
ROLE_ORDER = (
    RoleEnum.ADMIN.value,
    RoleEnum.TREASURER.value,
    RoleEnum.YARD_MANAGER.value,
    RoleEnum.USER.value,
    RoleEnum.READONLY.value,
)


def get_selectable_roles(user: User) -> list[str]:
    """Rôles que l'utilisateur peut choisir comme rôle actif.

    C'est-à-dire ses rôles attribués, plus tous ceux qu'ils impliquent : un
    administrateur peut ainsi travailler « en usager » pour éviter les fausses
    manœuvres, sans qu'on lui ait attribué explicitement le rôle usager.
    """
    assigned = set(get_authorized_roles(user))
    selectable = set(assigned)
    for r in assigned:
        selectable.update(ROLE_IMPLIES.get(r, ()))
    return [r for r in ROLE_ORDER if r in selectable]


def get_user_roles(user: User) -> list[str]:
    """Rôles EFFECTIFS pour les permissions : si un rôle actif est sélectionné
    (et sélectionnable), les droits sont limités à ce seul rôle ; sinon tous
    les rôles attribués."""
    active = getattr(user, "active_role", None)
    if active and active in get_selectable_roles(user):
        return [active]
    return get_authorized_roles(user)


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
