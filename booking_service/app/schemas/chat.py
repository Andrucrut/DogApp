from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseModel


class ConversationRead(BaseModel):
    id: UUID
    booking_id: UUID
    owner_id: UUID
    walker_user_id: UUID
    created_at: datetime


class MessageCreate(BaseModel):
    body: str


class MessageRead(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_user_id: UUID
    body: str
    created_at: datetime
    read_at: datetime | None = None


class MessagePage(BaseModel):
    items: list[MessageRead]
    next_cursor: UUID | None = None
    has_more: bool


class ConversationSummary(BaseModel):
    conversation: ConversationRead
    last_message: MessageRead | None = None
    unread_count: int
