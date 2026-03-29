from datetime import date, datetime, timezone
from uuid import UUID as PY_UUID

from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    String,
    Text,
    DateTime,
    func,
    event,
    inspect,
)
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UserStatus


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = "user"

    role_id: Mapped[PY_UUID] = mapped_column(ForeignKey("role.id"))
    avatar: Mapped[PY_UUID | None] = mapped_column(UUID)
    email: Mapped[str | None] = mapped_column(String, unique=True)
    phone: Mapped[str | None] = mapped_column(String, unique=True)
    telegram: Mapped[str | None] = mapped_column(String)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    middle_name: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    birth_date: Mapped[date | None] = mapped_column(Date)
    gender: Mapped[str | None] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String)
    city: Mapped[str | None] = mapped_column(String)
    api_token: Mapped[str | None] = mapped_column(Text)
    consent_personal_data: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    consent_privacy_policy: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        ENUM(
            UserStatus,
            name="user_status",
        ),
        server_default=UserStatus.ACTIVE,
    )
    password_updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint("consent_personal_data = TRUE", name="consent_personal_data_true"),
        CheckConstraint("consent_privacy_policy = TRUE", name="consent_privacy_policy_true"),
    )

    role = relationship("Role", back_populates="users", lazy="joined")


@event.listens_for(User, "before_update")
def update_password_timestamp(mapper, connection, target):
    state = inspect(target)
    if state.attrs.hashed_password.history.has_changes():
        target.password_updated_at = datetime.now(timezone.utc)
