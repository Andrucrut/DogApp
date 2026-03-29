from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseModel


class ReviewCreate(BaseModel):
    booking_id: UUID
    rating: int = Field(..., ge=1, le=5)
    comment: str | None = None


class ReviewRead(BaseModel):
    id: UUID
    booking_id: UUID
    reviewer_owner_id: UUID
    walker_profile_id: UUID
    rating: int
    comment: str | None
    created_at: datetime
