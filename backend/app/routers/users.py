"""Routes — Authentification et gestion des utilisateurs."""

import csv
import io
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update

from app.database import get_db
from app.models.user import User, UserRole, RoleEnum, PasswordResetToken
from app.models.visit import Visit
from app.models.apiary import hive_managers
from app.models.honey import HoneyHarvest, HoneyJar, HoneySale
from app.models.inventory import InventoryItem, InventoryMovement
from app.models.sanitary import SanitaryRecord
from app.models.treasury import Transaction
from app.models.audit import AuditLog
from app.schemas.user import (
    UserCreate, UserUpdate, UserOut, LoginRequest, Token, PasswordReset, SelfPasswordChange,
    SwitchRoleIn, MyProfileUpdate, ForgotPasswordIn, ResetPasswordIn,
)
from app.utils.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, require_roles, get_user_roles, get_authorized_roles,
    get_selectable_roles,
)
from app.utils.audit import log_action
from app.utils import mailer, password_reset as pwreset
from app.routers.settings import load_mail

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
    selectable = get_selectable_roles(user)
    active = user.default_role if user.default_role in selectable else None
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

    Le rôle demandé doit être sélectionnable : un rôle attribué, ou un rôle
    moins étendu qu'il implique (un admin peut travailler « en usager »).
    """
    role = body.role
    if role is not None and role not in get_selectable_roles(user):
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
    if body.role is not None and body.role not in get_selectable_roles(user):
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


# ═══════════════════════════════════════════════════════════════════
# Mot de passe oublié — réinitialisation en autonomie
# ═══════════════════════════════════════════════════════════════════

# Réponse volontairement identique dans tous les cas : un message différent
# selon que le compte existe ou non transformerait ce formulaire en annuaire
# des adhérents.
_NEUTRAL = ("Si un compte correspond, un e-mail contenant un lien de "
            "réinitialisation vient d'être envoyé. Pensez à regarder vos "
            "courriers indésirables.")


@router.post("/password-reset/request")
async def request_password_reset(
    body: ForgotPasswordIn,
    db: AsyncSession = Depends(get_db),
):
    """Envoie un lien de réinitialisation à l'adresse du compte.

    Accessible sans être connecté — c'est tout l'intérêt. L'identifiant de
    connexion comme l'adresse e-mail sont acceptés : personne ne se souvient
    lequel des deux il a donné.
    """
    cfg = await load_mail(db)
    if not mailer.mail_enabled(cfg):
        # Ici on peut être explicite : l'information ne concerne pas un compte
        # en particulier, et laisser l'adhérent attendre un e-mail qui ne
        # partira jamais serait pire.
        raise HTTPException(
            503,
            "L'envoi d'e-mails n'est pas configuré sur ce serveur : demandez à "
            "un administrateur de réinitialiser votre mot de passe.",
        )

    user = await pwreset.find_account(db, body.identifier)
    if not user or not user.is_active or not user.contact_email:
        # Compte inconnu, désactivé, ou sans adresse enregistrée : on ne dit
        # rien de plus, mais on laisse une trace côté serveur pour que
        # l'administrateur puisse comprendre un appel à l'aide.
        print(f"ℹ️  Réinitialisation demandée sans suite pour « {body.identifier} »")
        return {"detail": _NEUTRAL}

    if await pwreset.too_many_requests(db, user):
        print(f"⚠️  Réinitialisation : trop de demandes pour {user.email}")
        return {"detail": _NEUTRAL}

    token = await pwreset.create_token(db, user)
    base = (cfg.get("app_base_url") or "").rstrip("/")
    link = f"{base}/reinitialiser-mot-de-passe?token={token}"
    subject, html, text = pwreset.build_email(user, link)

    await log_action(db, user.id, "password_reset_request", "user", user.id)
    await db.flush()

    try:
        await mailer.send_mail(subject, html, text, [user.contact_email], cfg)
    except Exception as e:
        # L'échec d'envoi ne doit pas révéler que le compte existe ; il est en
        # revanche visible dans les journaux du serveur.
        print(f"❌ Réinitialisation : envoi impossible à {user.contact_email} — {e}")
    return {"detail": _NEUTRAL}


@router.get("/password-reset/check")
async def check_password_reset(
    token: str,
    db: AsyncSession = Depends(get_db),
):
    """Dit si un lien est encore utilisable, sans le consommer.

    Permet d'afficher tout de suite « ce lien a expiré » plutôt que de laisser
    saisir un mot de passe pour rien.
    """
    return {"valid": await pwreset.token_is_valid(db, token)}


@router.post("/password-reset/confirm", response_model=Token)
async def confirm_password_reset(
    body: ResetPasswordIn,
    db: AsyncSession = Depends(get_db),
):
    """Applique le nouveau mot de passe et connecte immédiatement l'adhérent."""
    if len(body.new_password or "") < 6:
        raise HTTPException(400, "Le nouveau mot de passe doit faire au moins 6 caractères")

    user = await pwreset.consume_token(db, body.token)
    if not user:
        raise HTTPException(
            400,
            "Ce lien n'est plus valable : il a expiré ou a déjà été utilisé. "
            "Demandez-en un nouveau.",
        )

    user.hashed_password = hash_password(body.new_password)
    # Déconnecte tous les appareils : si le mot de passe avait été compromis,
    # les sessions ouvertes ailleurs doivent tomber.
    user.token_version = (user.token_version or 0) + 1
    await log_action(db, user.id, "password_reset", "user", user.id)
    await db.flush()

    # L'adhérent qui vient de prouver l'accès à sa boîte mail est connecté
    # directement : le renvoyer vers la mire pour ressaisir ce qu'il vient de
    # choisir n'apporte rien.
    selectable = get_selectable_roles(user)
    active = user.default_role if user.default_role in selectable else None
    token = create_access_token({
        "sub": user.id, "username": user.email, "active_role": active,
        "tv": user.token_version,
    })
    return {"access_token": token, "token_type": "bearer"}


@router.put("/me/profile", response_model=UserOut)
async def update_my_profile(
    body: MyProfileUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Chacun tient à jour son adresse e-mail et son téléphone."""
    data = body.model_dump(exclude_unset=True)
    if data.get("contact_email"):
        await _check_contact_email_free(db, data["contact_email"], exclude_id=user.id)
    for k, v in data.items():
        setattr(user, k, v)
    await log_action(db, user.id, "update", "user", user.id, details="profil")
    await db.flush()
    await db.refresh(user)
    return _user_to_out(user)


async def _check_contact_email_free(db: AsyncSession, email: str, exclude_id: int = None):
    """Une adresse ne doit désigner qu'un compte : sinon la réinitialisation
    deviendrait ambiguë et pourrait viser le mauvais adhérent."""
    q = select(User).where(func.lower(User.contact_email) == email.lower())
    if exclude_id:
        q = q.where(User.id != exclude_id)
    other = (await db.execute(q.limit(1))).scalar_one_or_none()
    if other:
        raise HTTPException(
            409,
            f"L'adresse « {email} » est déjà associée au compte « {other.email} ».",
        )


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
    if body.contact_email:
        await _check_contact_email_free(db, body.contact_email)

    user = User(
        email=ident,
        contact_email=body.contact_email,
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

    changes = body.model_dump(exclude_unset=True)
    if changes.get("contact_email"):
        await _check_contact_email_free(db, changes["contact_email"], exclude_id=user.id)
    for field, value in changes.items():
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


# Ce qu'un compte laisse derrière lui. Ces enregistrements décrivent la vie de
# l'association — une récolte, une écriture comptable, un traitement inscrit au
# registre sanitaire — et doivent survivre au départ de la personne. Supprimer
# le compte les détruirait ou, pire, les priverait de leur auteur : on refuse
# donc, en disant précisément ce qui retient.
DELETION_BLOCKERS = [
    (Visit, Visit.author_id, "visite saisie", "visites saisies"),
    (HoneyHarvest, HoneyHarvest.created_by, "récolte de miel", "récoltes de miel"),
    (HoneyJar, HoneyJar.created_by, "mise en pot", "mises en pot"),
    (HoneySale, HoneySale.sold_by, "vente de miel", "ventes de miel"),
    (SanitaryRecord, SanitaryRecord.performed_by,
     "acte au registre sanitaire", "actes au registre sanitaire"),
    (Transaction, Transaction.created_by,
     "écriture de trésorerie", "écritures de trésorerie"),
    (InventoryMovement, InventoryMovement.performed_by,
     "mouvement de stock", "mouvements de stock"),
    # Le matériel personnel n'empêche pas techniquement la suppression, mais
    # son propriétaire deviendrait « l'association » : ce serait un transfert
    # de propriété silencieux.
    (InventoryItem, InventoryItem.owner_user_id,
     "matériel personnel", "matériels personnels"),
]


async def deletion_blockers(db: AsyncSession, user_id: int) -> list[dict]:
    """Liste, avec leur nombre, les éléments qui empêchent la suppression."""
    out = []
    for model, column, singular, plural in DELETION_BLOCKERS:
        n = await db.scalar(
            select(func.count()).select_from(model).where(column == user_id)
        ) or 0
        if n:
            out.append({"count": n, "label": singular if n == 1 else plural})
    return out


def _blockers_sentence(blockers: list[dict]) -> str:
    return ", ".join(f"{b['count']} {b['label']}" for b in blockers)


@router.get("/{user_id}/deletion-check")
async def check_user_deletion(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Dit si un compte peut être supprimé, et sinon ce qui le retient.

    Interrogé à l'ouverture de la boîte de dialogue : mieux vaut proposer
    d'emblée la bonne action que laisser cliquer sur « Supprimer » pour se
    heurter à une erreur de base de données.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, "Utilisateur introuvable")

    blockers = await deletion_blockers(db, user_id)
    warnings = []

    if user_id == current.id:
        warnings.append("Vous ne pouvez pas supprimer votre propre compte.")

    if RoleEnum.ADMIN.value in get_user_roles(user):
        admin_count = await db.scalar(
            select(func.count(func.distinct(UserRole.user_id)))
            .where(UserRole.role == RoleEnum.ADMIN)
        ) or 0
        if admin_count <= 1:
            warnings.append("C'est le dernier administrateur : le compte ne peut pas être supprimé.")

    managed = await db.scalar(
        select(func.count()).select_from(hive_managers)
        .where(hive_managers.c.user_id == user_id)
    ) or 0
    if managed and not blockers:
        warnings.append(
            f"{managed} ruche(s) resteraient sans responsable : pensez à en désigner un autre."
        )

    blocked = bool(blockers) or user_id == current.id or any(
        "dernier administrateur" in w for w in warnings
    )
    return {
        "deletable": not blocked,
        "blockers": blockers,
        "warnings": warnings,
        "is_active": user.is_active,
        "managed_hives": managed,
    }


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

    # Contrôle complet : jusqu'ici seules les visites étaient vérifiées, et une
    # récolte ou une écriture comptable faisait échouer la requête sur une
    # erreur de contrainte incompréhensible pour l'utilisateur.
    blockers = await deletion_blockers(db, user_id)
    if blockers:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Ce compte ne peut pas être supprimé : il a laissé "
                f"{_blockers_sentence(blockers)}. Ces enregistrements font partie "
                f"de l'historique de l'association et doivent conserver leur auteur. "
                f"Désactivez le compte : la personne ne pourra plus se connecter, "
                f"et tout son historique reste en place."
            ),
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
    """Import CSV : colonnes attendues = email, first_name, last_name, phone,
    roles (séparés par |), et facultativement contact_email (adresse réelle).

    Rappel : la colonne « email » porte l'**identifiant de connexion**, pas
    l'adresse. C'est « contact_email » qui reçoit l'adresse e-mail.
    """
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

            contact = (row.get("contact_email") or "").strip().lower() or None
            if contact:
                dup = await db.execute(
                    select(User).where(func.lower(User.contact_email) == contact)
                )
                if dup.scalar_one_or_none():
                    errors.append(f"Ligne {i}: l'adresse {contact} est déjà utilisée")
                    continue

            user = User(
                email=email,
                contact_email=contact,
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
        contact_email=user.contact_email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone=user.phone,
        is_active=user.is_active,
        roles=get_authorized_roles(user),          # tous les rôles attribués
        selectable_roles=get_selectable_roles(user),  # + rôles moins étendus
        active_role=getattr(user, "active_role", None),
        default_role=user.default_role,
        created_at=user.created_at,
    )
