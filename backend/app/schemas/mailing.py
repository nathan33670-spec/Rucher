"""Schémas Pydantic — Campagnes d'e-mail."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AudienceOut(BaseModel):
    """Public possible, avec le nombre d'adhérents réellement joignables."""
    key: str
    label: str
    count: int


class RecipientOut(BaseModel):
    id: int
    name: Optional[str] = None
    email: str
    sent: bool = False
    error: Optional[str] = None
    first_opened_at: Optional[datetime] = None
    last_opened_at: Optional[datetime] = None
    open_count: int = 0


class CampaignOut(BaseModel):
    id: int
    subject: str
    audience: str
    audience_label: str
    tracking: bool = True
    sent_at: Optional[datetime] = None
    sent_count: int = 0
    failed_count: int = 0
    opened_count: int = 0
    attachments_count: int = 0
    author_name: Optional[str] = None


class CampaignDetail(CampaignOut):
    body: str = ""
    attachments: list[dict] = []
    recipients: list[RecipientOut] = []
    attachments_count: int = 0
