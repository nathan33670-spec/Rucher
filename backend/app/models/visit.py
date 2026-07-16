"""Modèle Visite de ruche."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from app.database import Base


class Visit(Base):
    __tablename__ = "visits"
    id = Column(Integer, primary_key=True, index=True)
    hive_id = Column(Integer, ForeignKey("hives.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    visited_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    queen_seen = Column(Boolean)
    brood_score = Column(Integer)       # 0-9
    reserves_score = Column(Integer)    # 0-9, null = N/A (corps non ouvert)
    supers_count = Column(Integer)      # nombre de hausses actuel
    supers_delta = Column(Integer, default=0)  # +1/-1 (legacy)
    feeding = Column(String(200))
    comment = Column(Text)
    is_alert = Column(Boolean, default=False)
    alert_message = Column(String(500))
    honey_harvest_kg = Column(Float)
    pollen_harvest_kg = Column(Float)
    is_live_mode = Column(Boolean, default=False)
    synced = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hive = relationship("Hive", back_populates="visits")
    author = relationship("User", back_populates="visits")
