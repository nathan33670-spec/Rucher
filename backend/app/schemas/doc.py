"""Schémas Pydantic — Pages de documentation."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocPageCreate(BaseModel):
    title: str
    category: str = "Divers"
    content: str = ""
    is_published: bool = True
    sort_order: int = 100
    slug: Optional[str] = None  # auto-généré depuis le titre si absent


class DocPageUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    content: Optional[str] = None
    is_published: Optional[bool] = None
    sort_order: Optional[int] = None


class DocPageOut(BaseModel):
    id: int
    slug: str
    title: str
    category: str
    content: str
    is_published: bool
    sort_order: int
    updated_at: datetime
    class Config:
        from_attributes = True


class DocPageListItem(BaseModel):
    slug: str
    title: str
    category: str
    sort_order: int
    class Config:
        from_attributes = True
