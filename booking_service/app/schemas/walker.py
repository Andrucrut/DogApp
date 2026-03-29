from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.schemas.base import BaseModel


class WalkerRead(BaseModel):
    id: UUID
    user_id: UUID
    bio: str | None = None
    experience_years: int
    price_per_hour: Decimal
    latitude: float | None = None
    longitude: float | None = None
    service_radius_km: float
    is_verified: bool
    is_available: bool
    rating: float
    reviews_count: int
    created_at: datetime


class WalkerCreate(BaseModel):
    bio: str | None = None
    experience_years: int | None = None
    price_per_hour: Decimal
    latitude: float | None = None
    longitude: float | None = None
    service_radius_km: float = 5.0


class WalkerUpdate(BaseModel):
    bio: str | None = None
    experience_years: int | None = None
    price_per_hour: Decimal | None = None
    latitude: float | None = None
    longitude: float | None = None
    service_radius_km: float | None = None
    is_available: bool | None = None