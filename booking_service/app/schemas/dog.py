from datetime import date, datetime
from uuid import UUID

from pydantic import field_validator

from app.schemas.base import BaseModel


class DogRead(BaseModel):
    id: UUID
    owner_id: UUID
    name: str
    breed: str | None = None
    birth_date: date | None = None
    weight_kg: float | None = None
    gender: str | None = None
    is_vaccinated: bool
    is_sterilized: bool
    is_aggressive: bool
    medical_notes: str | None = None
    behavior_notes: str | None = None
    created_at: datetime


class DogCreate(BaseModel):
    name: str
    breed: str | None = None
    birth_date: date | None = None
    weight_kg: float | None = None
    gender: str | None = None
    is_vaccinated: bool = False
    is_sterilized: bool = False
    is_aggressive: bool = False
    medical_notes: str | None = None
    behavior_notes: str | None = None

    @field_validator("weight_kg")
    @classmethod
    def validate_weight(cls, v: float | None) -> float | None:
        if v is not None and v <= 0:
            raise ValueError("Вес должен быть больше 0")
        return v


class DogUpdate(BaseModel):
    name: str | None = None
    breed: str | None = None
    birth_date: date | None = None
    weight_kg: float | None = None
    gender: str | None = None
    is_vaccinated: bool | None = None
    is_sterilized: bool | None = None
    is_aggressive: bool | None = None
    medical_notes: str | None = None
    behavior_notes: str | None = None
