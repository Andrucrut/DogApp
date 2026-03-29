from uuid import UUID as PY_UUID

from sqlalchemy import Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Review(Base):
    __table_args__ = (UniqueConstraint("booking_id", name="uq_review_booking_id"),)

    booking_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    reviewer_owner_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    walker_profile_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
