from decimal import Decimal
from enum import auto
from uuid import UUID as PY_UUID

from sqlalchemy import Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column
from strenum import StrEnum

from app.db.base import Base


class PaymentStatus(StrEnum):
    PENDING = auto()
    REQUIRES_ACTION = auto()
    SUCCEEDED = auto()
    FAILED = auto()
    REFUNDED = auto()


class Payment(Base):
    __table_args__ = (UniqueConstraint("booking_id", name="uq_payment_booking_id"),)

    booking_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    payer_owner_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    beneficiary_walker_user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)

    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="RUB")

    status: Mapped[PaymentStatus] = mapped_column(
        ENUM(PaymentStatus, name="payment_status"),
        default=PaymentStatus.PENDING,
    )
    provider: Mapped[str] = mapped_column(String(64), default="mock_yookassa")
    external_payment_id: Mapped[str | None] = mapped_column(String(255))
    failure_reason: Mapped[str | None] = mapped_column(Text)
