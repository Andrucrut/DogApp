from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseModel


class AddressSuggestion(BaseModel):
    label: str
    country: str | None = None
    city: str | None = None
    street: str | None = None
    house: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class AddressSuggestResponse(BaseModel):
    items: list[AddressSuggestion]

