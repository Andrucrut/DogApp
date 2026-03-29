from datetime import datetime
from enum import auto
from uuid import UUID as PY_UUID

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from strenum import StrEnum

from app.db.base import Base


class WalkSessionStatus(StrEnum):
    LIVE = auto()
    COMPLETED = auto()
    CANCELLED = auto()


class WalkSession(Base):
    __table_args__ = (UniqueConstraint("booking_id", name="uq_walk_session_booking_id"),)

    booking_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    owner_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    walker_user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)

    status: Mapped[WalkSessionStatus] = mapped_column(
        ENUM(WalkSessionStatus, name="walk_session_status"),
        default=WalkSessionStatus.LIVE,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    points = relationship("TrackPoint", back_populates="session")
