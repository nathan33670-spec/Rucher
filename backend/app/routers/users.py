"""Routes — Authentification et gestion des utilisateurs."""

import csv
import io
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.models.user import User, UserRole, RoleEnum
from app.models.visit import Visit
from app.models.audit import AuditLog
from app.schemas.user import (
    UserCreate, UserUpdate, UserOut, LoginRequest, Token, PasswordReset, SelfPasswordChange,
    SwitchRoleIn,
)
from app.utils.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_roles, get_user_roles, get_authorized_roles,
)
from app.utils.audit import log_action

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/login", response_model=Token)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    # Connexion par nom d'utilisateur (identifiant). L'identifiant est stocké
    # dans la colonne « email » ; la comparaison est insensible à la casse.
    ident = body.username.strip()
    result = await db.execute(select(User).where(func.lower(User.email) == ident.lower()))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Identifiant ou mot de passe incorrect")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Compte désactivé")
    # Rôle actif = rôle par défaut de l'utilisateur (s'il est autorisé), sinon tous.
    authorized = get_authorized_roles(user)
    active = user.default_role if user.default_role in authorized else None
    # « Rester connecté » → jeton quasi-permanent (10 ans) ; sinon durée par défaut.
    expires = timedelta(days=3650) if body.remember else None
    token = create_access_token(
        {"sub": user.id, "username": user.email, "active_role": active,
         "tv": user.token_version or 0},
        expires_delta=expires,
    )
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)):
    return _user_to_out(user)


@router.post("/switch-role", response_model=Token)
async def switch_role(
    body: SwitchRoleIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Change le rôle actif « à la volée » (émet un nouveau jeton).
    Le rôle demandé doit faire partie des rôles autorisés de l'utilisateur."""
    authorized = get_authorized_roles(user)
    role = body.role
    if role is not None and role not in authorized:
        raise HTTPException(403, "Rôle non autorisé")
    token = create_access_token({"sub": user.id, "username": user.email, "active_role": role,
                                 "tv": user.token_version or 0})
    return {"access_token": token, "token_type": "bearer"}


@router.put("/me/default-role", response_model=UserOut)
async def set_default_role(
    body: SwitchRoleIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Définit le rôle actif par défaut (appliqué aux prochaines connexions)."""
    authorized = get_authorized_roles(user)
    if body.role is not None and body.role not in authorized:
        raise HTTPException(403, "Rôle non autorisé")
    user.default_role = body.role
    await db.flush()
    await db.refresh(user)
    return _user_to_out(user)


@router.put("/me/password")
async def change_my_password(
    body: SelfPasswordChange,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Permet à l'utilisateur courant de changer son propre mot de passe."""
    if not verify_password(body.current_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
    if len(body.new_password or "") < 6:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit faire au moins 6 caractères")
    user.hashed_password = hash_password(body.new_password)
    # Périme tous les jetons existants (y compris ceux des autres appareils).
    user.token_version = (user.token_version or 0) + 1
    await log_action(db, user.id, "password_change", "user", user.id)
    await db.flush()
    # Nouveau jeton pour l'appareil courant : l'utilisateur reste connecté ici.
    token = create_access_token({
        "sub": user.id, "username": user.email,
        "active_role": getattr(user, "active_role", None),
        "tv": user.token_version,
    })
    return {"detail": "Mot de passe modifié", "access_token": token, "token_type": "bearer"}


@router.get("/", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    result = await db.execute(select(User).order_by(User.last_name))
    return [_user_to_out(u) for u in result.scalars().all()]


@router.post("/", response_model=UserOut, status_code=201)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    # Vérifier unicité de l'identifiant (insensible à la casse)
    ident = body.email.strip()
    existing = await db.execute(select(User).where(func.lower(User.email) == ident.lower()))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Identifiant déjà utilisé")

    user = User(
        email=ident,
        hashed_password=hash_password(body.password),
        first_name=body.first_name,
        last_name=body.last_name,
        phone=body.phone,
    )
    db.add(user)
    await db.flush()

    for role in body.roles:
        db.add(UserRole(user_id=user.id, role=role))

    await log_action(db, current.id, "create", "user", user.id)
    await db.flush()
    await db.refresh(user)
    return _user_to_out(user)


@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    for field, value in body.model_dump(exclude_unset=True).items():
        if field == "roles":
            # Supprimer les anciens rôles et recréer
            for r in list(user.roles):
                await db.delete(r)
            await db.flush()
            for role in value:
                db.add(UserRole(user_id=user.id, role=role))
        else:
            setattr(user, field, value)

    await log_action(db, current.id, "update", "user", user.id)
    await db.flush()

    # Recharger
    await db.refresh(user)
    return _user_to_out(user)


@router.put("/{user_id}/password")
async def reset_password(
    user_id: int,
    body: PasswordReset,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.hashed_password = hash_password(body.new_password)
    # Déconnecte le compte concerné de tous ses appareils.
    user.token_version = (user.token_version or 0) + 1
    await log_action(db, current.id, "password_reset", "user", user.id)
    return {"detail": "Mot de passe modifié — le compte a été déconnecté de tous ses appareils"}


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Supprime définitivement un utilisateur (admin uniquement)."""
    if user_id == current.id:
        raise HTTPException(status_code=400, detail="Vous ne pouvez pas supprimer votre propre compte")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")

    # Un utilisateur ayant saisi des visites ne peut pas être supprimé
    # (author_id est NOT NULL, sans cascade) — on invite à le désactiver.
    visit_count = await db.scalar(
        select(func.count()).select_from(Visit).where(Visit.author_id == user_id)
    )
    if visit_count:
        raise HTTPException(
            status_code=400,
            detail=f"Impossible de supprimer : {visit_count} visite(s) saisie(s) par cet utilisateur. Désactivez le compte à la place.",
        )

    # Ne jamais supprimer le dernier administrateur
    if RoleEnum.ADMIN.value in get_user_roles(user):
        admin_count = await db.scalar(
            select(func.count(func.distinct(UserRole.user_id))).where(UserRole.role == RoleEnum.ADMIN)
        )
        if not admin_count or admin_count <= 1:
            raise HTTPException(status_code=400, detail="Impossible de supprimer le dernier administrateur")

    # Détacher les entrées du journal d'audit (user_id nullable), puis supprimer
    # (rôles et liens gestionnaire-ruche supprimés en cascade).
    await db.execute(update(AuditLog).where(AuditLog.user_id == user_id).values(user_id=None))
    await db.delete(user)
    await db.flush()
    await log_action(db, current.id, "delete", "user", user_id)
    return {"detail": "Utilisateur supprimé"}


@router.post("/import-csv", status_code=201)
async def import_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Import CSV: colonnes attendues = email, first_name, last_name, phone, roles (séparées par |)."""
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))
    created = 0
    errors = []
    for i, row in enumerate(reader, start=2):
        try:
            email = row["email"].strip()
            existing = await db.execute(select(User).where(User.email == email))
            if existing.scalar_one_or_none():
                errors.append(f"Ligne {i}: {email} existe déjà")
                continue

            roles_str = row.get("roles", "user").strip()
            role_list = [RoleEnum(r.strip()) for r in roles_str.split("|") if r.strip()]

            user = User(
                email=email,
                hashed_password=hash_password("changeme"),
                first_name=row.get("first_name", "").strip(),
                last_name=row.get("last_name", "").strip(),
                phone=row.get("phone", "").strip() or None,
            )
            db.add(user)
            await db.flush()

            for role in role_list:
                db.add(UserRole(user_id=user.id, role=role))

            created += 1
        except Exception as e:
            errors.append(f"Ligne {i}: {str(e)}")

    await log_action(db, current.id, "import_csv", "user", details=f"{created} créés")
    return {"created": created, "errors": errors}


def _user_to_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        is_active=user.is_active,
        roles=get_authorized_roles(user),          # tous les rôles autorisés
        active_role=getattr(user, "active_role", None),
        default_role=user.default_role,
        created_at=user.created_at,
    )
