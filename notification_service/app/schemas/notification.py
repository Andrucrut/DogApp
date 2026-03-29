from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseModel


class NotificationRead(BaseModel):
    id: UUID
    user_id: UUID
    title: str
    body: str
    data: dict | None
    channel: str
    read_at: datetime | None
    created_at: datetime


class InternalNotifyItem(BaseModel):
    user_id: UUID
    title: str
    body: str
    data: dict | None = None


class InternalNotifyBatch(BaseModel):
    items: list[InternalNotifyItem]


class InternalScheduleItem(BaseModel):
    user_id: UUID
    title: str
    body: str
    data: dict | None = None
    fire_at: datetime


class InternalScheduleBatch(BaseModel):
    items: list[InternalScheduleItem]


class CancelByBookingBody(BaseModel):
    booking_id: UUID
