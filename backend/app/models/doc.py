"""Modèle — Pages de documentation (créées/éditées par les admins)."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from app.database import Base


class DocPage(Base):
    __tablename__ = "doc_pages"
    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String(160), unique=True, nullable=False, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(100), default="Divers")
    content = Column(Text, default="")          # Markdown
    is_published = Column(Boolean, default=True)
    sort_order = Column(Integer, default=100)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
