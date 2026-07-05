"""Modèle Suivi sanitaire."""

import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class RecordType(str, enum.Enum):
    TREATMENT = "treatment"
    VARROA_COUNT = "varroa_count"


class SanitaryRecord(Base):
    __tablename__ = "sanitary_records"
    id = Column(Integer, primary_key=True, index=True)
    hive_id = Column(Integer, ForeignKey("hives.id", ondelete="CASCADE"), nullable=False)
    record_type = Column(String(50), default="treatment", nullable=False)
    treatment_type = Column(String(200))
    product = Column(String(200))
    dosage = Column(String(100))
    application_date = Column(Date, nullable=False)
    end_date = Column(Date)
    varroa_count = Column(Integer)
    notes = Column(Text)
    performed_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    hive = relationship("Hive", back_populates="sanitary_records")
