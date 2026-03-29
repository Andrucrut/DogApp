from datetime import datetime
from uuid import UUID as PY_UUID

from sqlalchemy import Boolean, DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[dict | None] = mapped_column(JSONB)
    channel: Mapped[str] = mapped_column(String(32), default="in_app")
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sent_push: Mapped[bool] = mapped_column(Boolean, default=False)
    sent_email: Mapped[bool] = mapped_column(Boolean, default=False)
