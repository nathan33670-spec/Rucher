"""
Rucher Manager — Point d'entrée FastAPI.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.database import engine, Base, async_session
from app.models import *  # noqa — charge tous les modèles
from app.models.user import User, UserRole, RoleEnum
from app.utils.auth import hash_password
from app.config import get_settings

from app.routers import users, apiaries, visits, inventory, treasury, sanitary, audit, honey, docs, visit_plans


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Crée les tables et le premier admin au démarrage."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Créer le premier admin si la table est vide
    settings = get_settings()
    async with async_session() as session:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is None:
            admin = User(
                email=settings.first_admin_email,
                hashed_password=hash_password(settings.first_admin_password),
                first_name="Admin",
                last_name="Rucher",
            )
            session.add(admin)
            await session.flush()
            session.add(UserRole(user_id=admin.id, role=RoleEnum.ADMIN))
            await session.commit()
            print(f"✅ Premier admin créé : {settings.first_admin_email}")

    yield


app = FastAPI(
    title="Rucher Manager API",
    description="API de gestion de rucher apicole",
    version="1.0.0",
    lifespan=lifespan,
)

# L'app est servie derrière nginx en same-origin ; l'authentification passe par
# un jeton Bearer (pas de cookie). On autorise donc toutes les origines SANS
# credentials (wildcard + credentials est invalide et rejeté par les navigateurs).
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(apiaries.router)
app.include_router(visits.router)
app.include_router(inventory.router)
app.include_router(treasury.router)
app.include_router(sanitary.router)
app.include_router(audit.router)
app.include_router(honey.router)
app.include_router(docs.router)
app.include_router(visit_plans.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "Rucher Manager"}
