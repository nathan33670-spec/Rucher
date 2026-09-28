"""Schémas Pydantic — Notifications push."""

from pydantic import BaseModel
from typing import Optional


class SubKeys(BaseModel):
    p256dh: str
    auth: str


class SubscribeIn(BaseModel):
    endpoint: str
    keys: SubKeys


class UnsubscribeIn(BaseModel):
    endpoint: str


class RotateIn(BaseModel):
    """Remplacement d'un abonnement que le navigateur a fait tourner."""
    old_endpoint: str
    endpoint: str
    keys: SubKeys


class PrefsOut(BaseModel):
    enabled: bool
    visits: bool
    visits_mine: bool = True
    visits_assoc: bool = True
    visits_private_others: bool = True
    inventory: bool
    alerts: bool
    sanitary: bool
    treasury: bool
    events: bool
    class Config:
        from_attributes = True


class PrefsUpdate(BaseModel):
    enabled: Optional[bool] = None
    visits: Optional[bool] = None
    visits_mine: Optional[bool] = None
    visits_assoc: Optional[bool] = None
    visits_private_others: Optional[bool] = None
    inventory: Optional[bool] = None
    alerts: Optional[bool] = None
    sanitary: Optional[bool] = None
    treasury: Optional[bool] = None
    events: Optional[bool] = None


class GeneralReportIn(BaseModel):
    """Signalement qui ne porte sur aucune ruche.

    ``apiary_id`` est facultatif : un signalement peut concerner un rucher
    précis (clôture, accès, voisinage) ou l'association en général.
    """
    message: str
    apiary_id: Optional[int] = None


class PrefsCapabilities(BaseModel):
    """Ce que cet adhérent a le droit d'activer.

    L'écran s'y fie pour n'afficher que les cases qui le concernent : une case
    cochable mais sans effet serait pire que pas de case du tout.
    """
    treasury: bool = False
    visits_private_others: bool = False
