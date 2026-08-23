"""Schémas Pydantic — Réglages de l'application."""

from pydantic import BaseModel, Field
from typing import Optional


class IdealCriteria(BaseModel):
    """Conditions d'un créneau « idéal » pour ouvrir les ruches."""
    hour_start: int = Field(10, ge=0, le=23)
    hour_end: int = Field(18, ge=0, le=23)
    temp_min: float = 15
    temp_max: float = 30
    rain_max: float = Field(30, ge=0, le=100)   # probabilité de pluie (%)
    wind_max: float = Field(25, ge=0)           # km/h
    min_hours: int = Field(2, ge=1, le=12)      # heures idéales requises dans la journée


class OkCriteria(BaseModel):
    """Conditions d'une journée « correcte » (à défaut d'idéale)."""
    temp_min: float = 12
    rain_max: float = Field(50, ge=0, le=100)
    wind_max: float = Field(35, ge=0)


class WeatherCriteria(BaseModel):
    ideal: IdealCriteria = IdealCriteria()
    ok: OkCriteria = OkCriteria()


class WeatherCriteriaUpdate(BaseModel):
    ideal: Optional[IdealCriteria] = None
    ok: Optional[OkCriteria] = None


class AccessSettings(BaseModel):
    """Réglages de cloisonnement entre adhérents."""
    # Trésorerie visible par tous les membres (lecture seule) ; par défaut
    # réservée aux administrateurs et trésoriers.
    treasury_read_all: bool = False
    # Journal d'activité visible par tous ; par défaut réservé aux admins.
    audit_read_all: bool = False


class AccessSettingsUpdate(BaseModel):
    treasury_read_all: Optional[bool] = None
    audit_read_all: Optional[bool] = None


class MailSettings(BaseModel):
    """Paramètres d'envoi d'e-mails, réglables depuis l'application."""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_tls: str = "starttls"        # starttls | ssl | none
    smtp_from: str = ""
    recipients: str = ""              # adresses séparées par des virgules
    digest_enabled: bool = True
    digest_weekday: int = Field(0, ge=0, le=6)
    digest_hour: int = Field(8, ge=0, le=23)
    app_base_url: str = ""


class MailSettingsOut(MailSettings):
    """Ce qui est renvoyé à l'interface : le mot de passe n'est jamais exposé."""
    password_set: bool = False
    source: str = "env"               # "env" | "app"


class MailSettingsUpdate(MailSettings):
    # Laisser vide conserve le mot de passe déjà enregistré.
    smtp_password: Optional[str] = None


class MailTestIn(BaseModel):
    to: Optional[str] = None          # destinataire du message de test
