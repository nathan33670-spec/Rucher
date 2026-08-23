"""Configuration de l'application via variables d'environnement."""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://rucher:rucher_secret_2026@postgres:5432/rucher"
    database_url_sync: str = "postgresql://rucher:rucher_secret_2026@postgres:5432/rucher"
    redis_url: str = "redis://redis:6379/0"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 43200  # 30 jours — évite les déconnexions fréquentes
    first_admin_email: str = "admin@rucher.local"
    first_admin_password: str = "admin1234"
    upload_dir: str = "/app/uploads"

    # ─── Envoi d'e-mails (récapitulatif hebdomadaire) ──────────────
    # Laisser smtp_host vide désactive complètement l'envoi.
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""              # expéditeur ; par défaut = smtp_user
    smtp_tls: str = "starttls"       # "starttls" | "ssl" | "none"

    # ─── Récapitulatif hebdomadaire ────────────────────────────────
    digest_enabled: bool = True
    # Destinataires séparés par des virgules. Les identifiants de connexion
    # ne sont PAS des adresses e-mail : la liste doit être renseignée ici.
    digest_recipients: str = ""
    digest_weekday: int = 0          # 0 = lundi … 6 = dimanche
    digest_hour: int = 8             # heure locale du serveur (0-23)
    # Adresse publique de l'application, pour le bouton du récapitulatif.
    app_base_url: str = ""

    class Config:
        env_file = ".env"


@lru_cache
def get_settings() -> Settings:
    return Settings()
