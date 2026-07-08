"""Amorçage (seed) idempotent des comptes de l'association.

Crée une première fois un jeu de comptes nommés (identifiant = nom simple, sans
e-mail). L'exécution est protégée par un marqueur en base (« app_settings ») :
les comptes ne sont créés qu'une seule fois par base de données. Si un
administrateur supprime ensuite un compte, il ne sera PAS recréé au redémarrage.
"""

from sqlalchemy import select, func

from app.models.user import User, UserRole, RoleEnum
from app.models.apiary import Apiary, Hive, OwnershipType, hive_managers
from app.models.notification import AppSetting
from app.utils.auth import hash_password

SEED_MARKER = "initial_accounts_seeded"

# Mot de passe initial commun — À CHANGER à la première connexion.
DEFAULT_PASSWORD = "rucher2026"

# (identifiant, prénom, nom, rôles)
ACCOUNTS = [
    ("paulin",       "Paulin",   "",      [RoleEnum.ADMIN]),
    ("luc",          "Luc",      "",      [RoleEnum.ADMIN]),
    ("marion",       "Marion",   "",      [RoleEnum.ADMIN]),
    ("isabelle",     "Isabelle", "",      [RoleEnum.ADMIN]),
    ("thomas",       "Thomas",   "",      [RoleEnum.USER]),
    ("thomas-admin", "Thomas",   "Admin", [RoleEnum.ADMIN]),
]


async def _get_or_create_user(session, ident, first_name, last_name, roles):
    res = await session.execute(
        select(User).where(func.lower(User.email) == ident.lower())
    )
    user = res.scalar_one_or_none()
    if user:
        return user
    user = User(
        email=ident,
        hashed_password=hash_password(DEFAULT_PASSWORD),
        first_name=first_name,
        last_name=last_name,
    )
    session.add(user)
    await session.flush()
    for role in roles:
        session.add(UserRole(user_id=user.id, role=role))
    await session.flush()
    return user


async def _ensure_thomas_owns_a_hive(session, thomas: User):
    """Garantit que « thomas » est gestionnaire d'au moins une ruche active."""
    already = await session.execute(
        select(hive_managers.c.hive_id).where(hive_managers.c.user_id == thomas.id)
    )
    if already.first():
        return

    # Utiliser le premier rucher existant, sinon en créer un de démonstration.
    apiary = (await session.execute(select(Apiary).order_by(Apiary.id).limit(1))).scalar_one_or_none()
    if not apiary:
        apiary = Apiary(name="Rucher de démonstration", address="Bois-d'Arcy")
        session.add(apiary)
        await session.flush()

    hive = Hive(
        apiary_id=apiary.id,
        name="Ruche de Thomas (démo)",
        ownership=OwnershipType.PRIVATE,
        status="active",
    )
    session.add(hive)
    await session.flush()
    await session.execute(
        hive_managers.insert().values(user_id=thomas.id, hive_id=hive.id)
    )


async def seed_initial_accounts(session):
    """Crée les comptes de l'association une seule fois (idempotent)."""
    marker = await session.get(AppSetting, SEED_MARKER)
    if marker:
        return

    created = {}
    for ident, first_name, last_name, roles in ACCOUNTS:
        created[ident] = await _get_or_create_user(session, ident, first_name, last_name, roles)

    thomas = created.get("thomas")
    if thomas:
        await _ensure_thomas_owns_a_hive(session, thomas)

    session.add(AppSetting(key=SEED_MARKER, value="1"))
    await session.commit()
