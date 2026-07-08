"""Modèles — Événements de l'association et réponses des adhérents (RSVP)."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
)
from app.database import Base


class Event(Base):
    """Un événement de l'association (visite de rucher, réunion, récolte…).

    Créé par un administrateur. « is_public » : visible par tous les adhérents
    (et ouvert au RSVP). Un événement privé n'est visible que des admins.
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(300), nullable=True)
    start_at = Column(DateTime, nullable=False, index=True)
    end_at = Column(DateTime, nullable=True)
    is_public = Column(Boolean, default=True, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventRSVP(Base):
    """Réponse d'un adhérent à un événement : yes / maybe / no. Modifiable."""
    __tablename__ = "event_rsvps"
    __table_args__ = (UniqueConstraint("event_id", "user_id", name="uq_rsvp_event_user"),)

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    response = Column(String(10), nullable=False)  # "yes" | "maybe" | "no"
    responded_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
