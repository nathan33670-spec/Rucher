"""Schémas Pydantic — Événements et réponses (RSVP)."""

from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, field_validator


RSVPResponse = Literal["yes", "maybe", "no"]


class EventBase(BaseModel):
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_at: datetime
    end_at: Optional[datetime] = None
    is_public: bool = True


class EventCreate(EventBase):
    # Notifier tous les adhérents (push) à la création.
    notify: bool = False


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    is_public: Optional[bool] = None


class RSVPCounts(BaseModel):
    yes: int = 0
    maybe: int = 0
    no: int = 0


class EventOut(EventBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    # Réponse de l'utilisateur courant ("yes"/"maybe"/"no") ou None
    my_response: Optional[str] = None
    counts: RSVPCounts = RSVPCounts()

    class Config:
        from_attributes = True


class RSVPIn(BaseModel):
    response: RSVPResponse


class ParticipantOut(BaseModel):
    user_id: int
    name: str
    email: Optional[str] = None
    response: str
    responded_at: Optional[datetime] = None
