from datetime import datetime
from uuid import UUID

from app.models.walk_session import WalkSessionStatus
from app.schemas.base import BaseModel


class WalkSessionStart(BaseModel):
    booking_id: UUID


class TrackPointIn(BaseModel):
    latitude: float
    longitude: float
    accuracy_m: int | None = None
    recorded_at: datetime | None = None


class TrackPointRead(BaseModel):
    id: UUID
    session_id: UUID
    latitude: float
    longitude: float
    accuracy_m: int | None
    recorded_at: datetime


class WalkSessionRead(BaseModel):
    id: UUID
    booking_id: UUID
    owner_id: UUID
    walker_user_id: UUID
    status: WalkSessionStatus
    started_at: datetime
    ended_at: datetime | None
    created_at: datetime
