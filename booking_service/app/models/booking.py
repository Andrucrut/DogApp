from datetime import datetime
from decimal import Decimal
from enum import auto
from strenum import StrEnum
from uuid import UUID as PY_UUID

from sqlalchemy import String, Date, Float, Boolean, Text, ForeignKey, DateTime, TIMESTAMP, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class BookingStatus(StrEnum):
    PENDING = auto()
    CONFIRMED = auto()
    IN_PROGRESS = auto()
    AWAITING_OWNER_PAYMENT = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class Booking(Base):
    owner_id: Mapped[PY_UUID] = mapped_column(UUID)
    walker_id: Mapped[PY_UUID | None] = mapped_column(ForeignKey('walker.id'), nullable=True)
    dog_id: Mapped[PY_UUID] = mapped_column(ForeignKey('dog.id'))

    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    price: Mapped[Decimal] = mapped_column(Numeric(10,2), default=Decimal("0.00"))

    address_country: Mapped[str | None] = mapped_column(String(128))
    address_city: Mapped[str | None] = mapped_column(String(128))
    address_street: Mapped[str | None] = mapped_column(String(256))
    address_house: Mapped[str | None] = mapped_column(String(64))
    address_apartment: Mapped[str | None] = mapped_column(String(64))
    meeting_latitude: Mapped[float | None] = mapped_column(Float)
    meeting_longitude: Mapped[float | None] = mapped_column(Float)

    status: Mapped[BookingStatus] = mapped_column(
        ENUM(BookingStatus, name="booking_status"),
        server_default=BookingStatus.PENDING,
    )

    owner_notes: Mapped[str | None] = mapped_column(Text)
    cancel_reason: Mapped[str | None] = mapped_column(Text)

    walker = relationship("Walker", back_populates="bookings")
    dog = relationship("Dog", back_populates="bookings")
    applications = relationship("BookingApplication", back_populates="booking")
    conversation = relationship("Conversation", back_populates="booking", uselist=False)


