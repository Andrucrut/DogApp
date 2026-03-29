from datetime import time

from sqlalchemy import ForeignKey, Integer, Time, Boolean

from app.db.base import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from uuid import UUID as PY_UUID


class Schedule(Base):
    walker_id: Mapped[PY_UUID] = mapped_column(ForeignKey('walker.id'))

    day_of_week: Mapped[int] = mapped_column(Integer)
    time_from: Mapped[time] = mapped_column(Time)
    time_to: Mapped[time] = mapped_column(Time)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    walker = relationship("Walker", back_populates="schedules")
