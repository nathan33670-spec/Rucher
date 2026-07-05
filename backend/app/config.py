"""Configuration de l'application via variables d'environnement."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://rucher:rucher_secret_2026@postgres:5432/rucher"
    database_url_sync: str = "postgresql://rucher:rucher_secret_2026@postgres:5432/rucher"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480
    first_admin_email: str = "admin@rucher.local"
    first_admin_password: str = "admin1234"
    upload_dir: str = "/app/uploads"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
