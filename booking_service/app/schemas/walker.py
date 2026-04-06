from datetime import datetime
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import model_validator

from app.core.geo import is_spb_point
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

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("walker_coordinates_incomplete")
        if self.latitude is not None and self.longitude is not None:
            if not is_spb_point(self.latitude, self.longitude):
                raise ValueError("walker_point_outside_supported_city")
        return self


class WalkerUpdate(BaseModel):
    bio: str | None = None
    experience_years: int | None = None
    price_per_hour: Decimal | None = None
    latitude: float | None = None
    longitude: float | None = None
    service_radius_km: float | None = None
    is_available: bool | None = None

    @model_validator(mode="after")
    def validate_location(self) -> Self:
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("walker_coordinates_incomplete")
        if self.latitude is not None and self.longitude is not None:
            if not is_spb_point(self.latitude, self.longitude):
                raise ValueError("walker_point_outside_supported_city")
        return self