from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.models.application import ApplicationStatus
from app.schemas.base import BaseModel


class BookingApplicationRead(BaseModel):
    id: UUID
    booking_id: UUID
    walker_id: UUID
    walker_user_id: UUID
    status: ApplicationStatus
    created_at: datetime
    walker_first_name: str | None = None
    walker_last_name: str | None = None
    walker_avatar: UUID | None = None
    walker_city: str | None = None
    walker_rating: float | None = None
    walker_reviews_count: int | None = None
    walker_price_per_hour: Decimal | None = None
    conversation_id: UUID | None = None


class ChooseApplicationBody(BaseModel):
    application_id: UUID
