from datetime import date
from uuid import UUID as PY_UUID

from sqlalchemy import String, Date, Float, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Dog(Base):
    owner_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)

    name: Mapped[str] = mapped_column(String, nullable=False)
    breed: Mapped[str | None] = mapped_column(String)
    birth_date: Mapped[date | None] = mapped_column(Date)
    weight_kg: Mapped[float | None] = mapped_column(Float)
    gender: Mapped[str | None] = mapped_column(String)

    is_vaccinated: Mapped[bool] = mapped_column(Boolean, default=False)
    is_sterilized: Mapped[bool] = mapped_column(Boolean, default=False)
    is_aggressive: Mapped[bool] = mapped_column(Boolean, default=False)

    medical_notes: Mapped[str | None] = mapped_column(Text)
    behavior_notes: Mapped[str | None] = mapped_column(Text)

    bookings = relationship("Booking", back_populates="dog")