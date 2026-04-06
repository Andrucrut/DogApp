from decimal import Decimal
from uuid import UUID as PY_UUID

from sqlalchemy import Text, Integer, Numeric, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID

from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Walker(Base):

    user_id: Mapped[PY_UUID] = mapped_column(UUID, unique=True)
    bio: Mapped[str | None] = mapped_column(Text)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    price_per_hour: Mapped[Decimal] = mapped_column(Numeric(10,2), default=Decimal("0.00"))

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    service_radius_km: Mapped[float] = mapped_column(Float, default=5.0)

    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    is_available: Mapped[bool] = mapped_column(Boolean, default=False)

    rating: Mapped[float] = mapped_column(Float, default=0.0)
    reviews_count: Mapped[int] = mapped_column(Integer, default=0)

    schedules = relationship("Schedule", back_populates="walker")
    bookings = relationship("Booking", back_populates="walker")
    applications = relationship("BookingApplication", back_populates="walker")