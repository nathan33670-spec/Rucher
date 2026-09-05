"""Modèles — Notifications push (abonnements, préférences) + réglages app."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, UniqueConstraint
from app.database import Base


class AppSetting(Base):
    """Paires clé/valeur persistantes (ex. clés VAPID)."""
    __tablename__ = "app_settings"
    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)


class PushSubscription(Base):
    """Un abonnement push par appareil/navigateur d'un utilisateur."""
    __tablename__ = "push_subscriptions"
    __table_args__ = (UniqueConstraint("endpoint", name="uq_push_endpoint"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint = Column(Text, nullable=False)
    p256dh = Column(Text, nullable=False)
    auth = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class NotificationPref(Base):
    """Préférences de notification d'un utilisateur (catégories)."""
    __tablename__ = "notification_prefs"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    enabled = Column(Boolean, default=True)          # interrupteur général
    visits = Column(Boolean, default=True)           # nouvelle visite
    inventory = Column(Boolean, default=True)        # mouvement de matériel
    alerts = Column(Boolean, default=True)           # alerte terrain
    sanitary = Column(Boolean, default=True)         # traitement / comptage
    treasury = Column(Boolean, default=False)        # écriture de trésorerie
    events = Column(Boolean, default=True)           # événement de l'association
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class InboxMessage(Base):
    """Notification consultable dans l'application (icône cloche).

    Le push est transitoire : il disparaît de l'écran, n'existe pas sur les
    appareils non abonnés et jamais sur un ordinateur de bureau. Cette table
    garde une trace durable de ce qui a été annoncé, consultable par chacun
    quand il le souhaite.
    """
    __tablename__ = "inbox_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                     nullable=False, index=True)
    category = Column(String(30), nullable=False, default="info")
    title = Column(String(200), nullable=False)
    body = Column(Text)
    url = Column(String(300))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    read_at = Column(DateTime, nullable=True)
