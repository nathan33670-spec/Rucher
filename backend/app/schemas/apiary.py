"""Schémas Pydantic — Rucher & Ruche."""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ApiaryCreate(BaseModel):
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class ApiaryUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None

class ApiaryOut(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    created_at: datetime
    hives_count: int = 0
    class Config:
        from_attributes = True


class HiveCreate(BaseModel):
    apiary_id: int
    napi_number: Optional[str] = None
    name: Optional[str] = None
    ownership: str = "associative"
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    status: str = "active"
    notes: Optional[str] = None
    manager_ids: list[int] = []
    photo: Optional[str] = None

class HiveUpdate(BaseModel):
    napi_number: Optional[str] = None
    name: Optional[str] = None
    ownership: Optional[str] = None
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    manager_ids: Optional[list[int]] = None
    photo: Optional[str] = None

class HiveOut(BaseModel):
    id: int
    apiary_id: int
    napi_number: Optional[str] = None
    name: Optional[str] = None
    ownership: str = "associative"
    position_x: Optional[float] = None
    position_y: Optional[float] = None
    status: str
    notes: Optional[str] = None
    managers: list[dict] = []
    photo_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True
