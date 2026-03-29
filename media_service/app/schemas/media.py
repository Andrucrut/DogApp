from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseModel


class MediaRead(BaseModel):
    id: UUID
    owner_user_id: UUID
    content_type: str
    size_bytes: int
    original_filename: str | None
    storage_key: str
    created_at: datetime
