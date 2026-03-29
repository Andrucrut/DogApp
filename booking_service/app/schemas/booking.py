from datetime import datetime, timedelta
from decimal import Decimal
from typing import Self
from uuid import UUID

from pydantic import field_validator, model_validator

from app.models.booking import BookingStatus
from app.schemas.base import BaseModel


class BookingRead(BaseModel):
    id: UUID
    owner_id: UUID
    walker_id: UUID | None = None
    dog_id: UUID
    scheduled_at: datetime
    duration_minutes: int
    price: Decimal
    status: BookingStatus
    address_country: str | None = None
    address_city: str | None = None
    address_street: str | None = None
    address_house: str | None = None
    address_apartment: str | None = None
    meeting_latitude: float | None = None
    meeting_longitude: float | None = None
    owner_notes: str | None = None
    cancel_reason: str | None = None
    created_at: datetime


class BookingCreate(BaseModel):
    walker_id: UUID | None = None
    dog_id: UUID
    scheduled_at: datetime
    duration_minutes: int
    address_country: str
    address_city: str
    address_street: str
    address_house: str | None = None
    address_apartment: str | None = None
    meeting_latitude: float | None = None
    meeting_longitude: float | None = None
    owner_notes: str | None = None

    @field_validator("duration_minutes")
    @classmethod
    def validate_duration_minutes(cls, v:int) -> int:
        if v < 15:
            raise ValueError("Минимальная длительность 15 минут")
        if v > 480:
            raise ValueError("Максимальная длительность 8 часов")
        return v

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_at(cls, v: datetime) -> datetime:
        if v < datetime.now(v.tzinfo):
            raise ValueError("Нельзя забронировать в прошлом")
        return v

    @model_validator(mode="after")
    def address_required(self) -> Self:
        if not self.address_country.strip():
            raise ValueError("country_required")
        if not self.address_city.strip():
            raise ValueError("city_required")
        if not self.address_street.strip():
            raise ValueError("street_required")
        return self


class BookingUpdate(BaseModel):
    owner_notes: str | None = None
    cancel_reason: str | None = None


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    cancel_reason: str | None = None

    @model_validator(mode="after")
    def cancel_reason_required(self) -> Self:
        if self.status == BookingStatus.CANCELLED and not self.cancel_reason:
            raise ValueError("При отмене нужно указать причину")
        return self