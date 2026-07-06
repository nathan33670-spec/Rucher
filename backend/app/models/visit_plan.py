"""Modèle — Jours de visite planifiés par l'utilisateur (préférences persistantes)."""

from datetime import datetime
from sqlalchemy import Column, Integer, Date, String, DateTime, ForeignKey, UniqueConstraint
from app.database import Base


class VisitPlan(Base):
    __tablename__ = "visit_plans"
    __table_args__ = (UniqueConstraint("user_id", "plan_date", name="uq_visitplan_user_date"),)

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    plan_date = Column(Date, nullable=False)
    note = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
