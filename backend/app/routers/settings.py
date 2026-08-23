"""Routes — Réglages de l'application (paramétrables par l'administrateur).

Les réglages sont stockés en JSON dans la table clé/valeur ``app_settings``,
ce qui évite une table dédiée (et donc une migration) par nouveau réglage.
"""

import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.notification import AppSetting
from app.models.user import User, RoleEnum
from app.schemas.settings import (
    WeatherCriteria, WeatherCriteriaUpdate,
    AccessSettings, AccessSettingsUpdate,
    MailSettingsOut, MailSettingsUpdate, MailTestIn,
)
from app.utils import mailer
from app.utils.auth import get_current_user, require_roles
from app.utils.audit import log_action

router = APIRouter(prefix="/api/settings", tags=["settings"])

WEATHER_KEY = "weather_criteria"
ACCESS_KEY = "access_settings"


async def _load_weather(db: AsyncSession) -> WeatherCriteria:
    """Critères enregistrés, ou valeurs par défaut si absents/illisibles."""
    row = await db.get(AppSetting, WEATHER_KEY)
    if not row:
        return WeatherCriteria()
    try:
        return WeatherCriteria.model_validate(json.loads(row.value))
    except Exception:
        # Réglage corrompu : on repart des valeurs par défaut plutôt que de
        # casser la page météo.
        return WeatherCriteria()


@router.get("/weather", response_model=WeatherCriteria)
async def get_weather_criteria(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lecture ouverte à tous : la page météo en a besoin pour classer les jours."""
    return await _load_weather(db)


@router.put("/weather", response_model=WeatherCriteria)
async def set_weather_criteria(
    body: WeatherCriteriaUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Mise à jour réservée aux administrateurs."""
    current = await _load_weather(db)
    merged = WeatherCriteria(
        ideal=body.ideal or current.ideal,
        ok=body.ok or current.ok,
    )
    if merged.ideal.hour_start > merged.ideal.hour_end:
        raise HTTPException(400, "L'heure de début doit précéder l'heure de fin")
    if merged.ideal.temp_min > merged.ideal.temp_max:
        raise HTTPException(400, "La température minimale doit être inférieure à la maximale")

    payload = json.dumps(merged.model_dump())
    row = await db.get(AppSetting, WEATHER_KEY)
    if row:
        row.value = payload
    else:
        db.add(AppSetting(key=WEATHER_KEY, value=payload))
    await log_action(db, user.id, "update", "settings", details=WEATHER_KEY)
    return merged


@router.delete("/weather", response_model=WeatherCriteria)
async def reset_weather_criteria(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Rétablit les critères par défaut."""
    row = await db.get(AppSetting, WEATHER_KEY)
    if row:
        await db.delete(row)
    await log_action(db, user.id, "reset", "settings", details=WEATHER_KEY)
    return WeatherCriteria()


# ═══════════════════════════════════════════════════════════════════
# Cloisonnement des accès
# ═══════════════════════════════════════════════════════════════════

async def load_access(db: AsyncSession) -> AccessSettings:
    """Réglages d'accès enregistrés, ou valeurs par défaut (les plus fermées)."""
    row = await db.get(AppSetting, ACCESS_KEY)
    if not row:
        return AccessSettings()
    try:
        return AccessSettings.model_validate(json.loads(row.value))
    except Exception:
        return AccessSettings()


@router.get("/access", response_model=AccessSettings)
async def get_access_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lecture ouverte : l'interface masque les onglets non autorisés."""
    return await load_access(db)


@router.put("/access", response_model=AccessSettings)
async def set_access_settings(
    body: AccessSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    current = await load_access(db)
    merged = AccessSettings(
        treasury_read_all=(current.treasury_read_all if body.treasury_read_all is None
                           else body.treasury_read_all),
        audit_read_all=(current.audit_read_all if body.audit_read_all is None
                        else body.audit_read_all),
    )
    payload = json.dumps(merged.model_dump())
    row = await db.get(AppSetting, ACCESS_KEY)
    if row:
        row.value = payload
    else:
        db.add(AppSetting(key=ACCESS_KEY, value=payload))
    await log_action(db, user.id, "update", "settings", details=ACCESS_KEY)
    return merged


# ═══════════════════════════════════════════════════════════════════
# Envoi d'e-mails — réglable depuis l'application
# ═══════════════════════════════════════════════════════════════════

MAIL_KEY = "mail_settings"

# Champs jamais renvoyés à l'interface.
_SECRET_FIELDS = {"smtp_password"}


async def load_mail(db: AsyncSession) -> dict:
    """Configuration effective : ce qui est réglé dans l'application prime
    sur les variables d'environnement. Permet de mettre l'envoi en service
    sans redéployer la pile."""
    cfg = mailer.env_config()
    row = await db.get(AppSetting, MAIL_KEY)
    if row:
        try:
            stored = json.loads(row.value)
            for k, v in stored.items():
                # Seul le mot de passe conserve l'ancienne valeur quand il est
                # laissé vide : pour les autres champs, vider depuis l'interface
                # doit réellement vider le réglage.
                if k in _SECRET_FIELDS and v in (None, ""):
                    continue
                cfg[k] = v
            cfg["source"] = "app"
        except Exception:
            pass
    return cfg


@router.get("/mail", response_model=MailSettingsOut)
async def get_mail_settings(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    cfg = await load_mail(db)
    return MailSettingsOut(
        smtp_host=cfg.get("smtp_host") or "",
        smtp_port=int(cfg.get("smtp_port") or 587),
        smtp_user=cfg.get("smtp_user") or "",
        smtp_tls=cfg.get("smtp_tls") or "starttls",
        smtp_from=cfg.get("smtp_from") or "",
        recipients=cfg.get("recipients") or "",
        digest_enabled=bool(cfg.get("digest_enabled", True)),
        digest_weekday=int(cfg.get("digest_weekday") or 0),
        digest_hour=int(cfg.get("digest_hour") or 8),
        app_base_url=cfg.get("app_base_url") or "",
        password_set=bool(cfg.get("smtp_password")),
        source=cfg.get("source", "env"),
    )


@router.put("/mail", response_model=MailSettingsOut)
async def set_mail_settings(
    body: MailSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    if body.smtp_tls not in ("starttls", "ssl", "none"):
        raise HTTPException(400, "Chiffrement invalide (starttls, ssl ou none)")

    row = await db.get(AppSetting, MAIL_KEY)
    stored = {}
    if row:
        try:
            stored = json.loads(row.value)
        except Exception:
            stored = {}

    data = body.model_dump(exclude={"smtp_password"})
    # Mot de passe laissé vide = on conserve celui déjà enregistré.
    if body.smtp_password:
        data["smtp_password"] = body.smtp_password
    elif stored.get("smtp_password"):
        data["smtp_password"] = stored["smtp_password"]

    payload = json.dumps(data)
    if row:
        row.value = payload
    else:
        db.add(AppSetting(key=MAIL_KEY, value=payload))
    await log_action(db, user.id, "update", "settings", details=MAIL_KEY)
    await db.flush()
    return await get_mail_settings(db=db, user=user)


@router.post("/mail/test")
async def test_mail_settings(
    body: MailTestIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(RoleEnum.ADMIN)),
):
    """Envoie un message de test avec la configuration enregistrée."""
    cfg = await load_mail(db)
    if not cfg.get("smtp_host"):
        raise HTTPException(400, "Renseignez d'abord un serveur SMTP.")

    targets = mailer.parse_recipients(body.to) or mailer.recipients(cfg)
    if not targets:
        raise HTTPException(400, "Aucun destinataire : renseignez une adresse de test.")

    html = (
        '<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;'
        'max-width:520px;margin:0 auto;padding:24px;">'
        '<div style="text-align:center;font-size:26px;">🐝</div>'
        '<h2 style="text-align:center;color:#2B2520;font-size:18px;">'
        'Configuration e-mail validée</h2>'
        '<p style="color:#4E443A;line-height:1.6;">Si vous lisez ce message, '
        'Rucher Manager peut envoyer des e-mails. Le récapitulatif hebdomadaire '
        'partira automatiquement au créneau choisi.</p></div>'
    )
    text = ("Configuration e-mail validée.\n\n"
            "Rucher Manager peut envoyer des e-mails. Le récapitulatif "
            "hebdomadaire partira automatiquement au créneau choisi.")
    try:
        sent = await mailer.send_mail("Rucher — test d'envoi", html, text, targets, cfg)
    except mailer.MailNotConfigured as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(502, f"Échec de l'envoi : {e}")
    return {"detail": f"Message de test envoyé à {', '.join(sent)}", "recipients": sent}
