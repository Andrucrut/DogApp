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


class WalkRouteSummary(BaseModel):
    points_count: int
    total_points: int
    returned_points: int
    offset: int
    limit: int
    has_more: bool
    total_distance_m: float
    started_at: datetime | None
    ended_at: datetime | None
    duration_seconds: int | None
    min_latitude: float | None
    max_latitude: float | None
    min_longitude: float | None
    max_longitude: float | None


class WalkRouteResponse(BaseModel):
    session: WalkSessionRead
    points: list[TrackPointRead]
    summary: WalkRouteSummary


class TrackPointPage(BaseModel):
    items: list[TrackPointRead]
    total: int
    offset: int
    limit: int
    has_more: bool
