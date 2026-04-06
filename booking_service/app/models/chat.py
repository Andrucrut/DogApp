from uuid import UUID as PY_UUID

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Conversation(Base):
    booking_id: Mapped[PY_UUID] = mapped_column(ForeignKey("booking.id"), nullable=False, unique=True)
    owner_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    walker_user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)

    booking = relationship("Booking", back_populates="conversation")
    messages = relationship("Message", back_populates="conversation")


class Message(Base):
    conversation_id: Mapped[PY_UUID] = mapped_column(ForeignKey("conversation.id"), nullable=False)
    sender_user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    conversation = relationship("Conversation", back_populates="messages")
