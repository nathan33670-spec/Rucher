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
from app.schemas.settings import WeatherCriteria, WeatherCriteriaUpdate
from app.utils.auth import get_current_user, require_roles
from app.utils.audit import log_action

router = APIRouter(prefix="/api/settings", tags=["settings"])

WEATHER_KEY = "weather_criteria"


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
