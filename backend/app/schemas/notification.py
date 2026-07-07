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


class PrefsOut(BaseModel):
    enabled: bool
    visits: bool
    inventory: bool
    alerts: bool
    sanitary: bool
    treasury: bool
    class Config:
        from_attributes = True


class PrefsUpdate(BaseModel):
    enabled: Optional[bool] = None
    visits: Optional[bool] = None
    inventory: Optional[bool] = None
    alerts: Optional[bool] = None
    sanitary: Optional[bool] = None
    treasury: Optional[bool] = None
