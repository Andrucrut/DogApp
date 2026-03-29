from datetime import time
from uuid import UUID

from app.schemas.base import BaseModel


class ScheduleCreate(BaseModel):
    day_of_week: int
    time_from: time
    time_to: time


class ScheduleUpdate(BaseModel):
    time_from: time | None = None
    time_to: time | None = None
    is_active: bool | None = None


class ScheduleRead(BaseModel):
    id: UUID
    walker_id: UUID
    day_of_week: int
    time_from: time
    time_to: time
    is_active: bool