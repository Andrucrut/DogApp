from enum import auto
from strenum import StrEnum
from uuid import UUID as PY_UUID

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class ApplicationStatus(StrEnum):
    PENDING = auto()
    WITHDRAWN = auto()
    ACCEPTED = auto()
    REJECTED = auto()


class BookingApplication(Base):
    booking_id: Mapped[PY_UUID] = mapped_column(ForeignKey("booking.id"), nullable=False)
    walker_id: Mapped[PY_UUID] = mapped_column(ForeignKey("walker.id"), nullable=False)
    walker_user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(
        ENUM(ApplicationStatus, name="application_status"),
        server_default=ApplicationStatus.PENDING,
        nullable=False,
    )

    booking = relationship("Booking", back_populates="applications")
    walker = relationship("Walker", back_populates="applications")
