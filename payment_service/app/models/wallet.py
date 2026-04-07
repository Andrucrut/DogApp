from decimal import Decimal
from enum import auto
from uuid import UUID as PY_UUID

from sqlalchemy import Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column
from strenum import StrEnum

from app.db.base import Base


class LedgerEntryKind(StrEnum):
    TOPUP = auto()
    OWNER_BOOKING_DEBIT = auto()
    WALKER_BOOKING_CREDIT = auto()
    WITHDRAWAL_RESERVE = auto()
    WITHDRAWAL_REJECT_REFUND = auto()


class WithdrawalStatus(StrEnum):
    PENDING_MODERATION = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    REJECTED = auto()


class Wallet(Base):
    user_id: Mapped[PY_UUID] = mapped_column(UUID, unique=True, nullable=False, index=True)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=Decimal("0.00"))
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RUB")


class WalletLedger(Base):
    user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False, index=True)
    kind: Mapped[LedgerEntryKind] = mapped_column(
        ENUM(LedgerEntryKind, name="ledger_entry_kind"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    booking_id: Mapped[PY_UUID | None] = mapped_column(UUID, nullable=True, index=True)
    withdrawal_id: Mapped[PY_UUID | None] = mapped_column(UUID, nullable=True)


class BookingWalletSettlement(Base):
    __table_args__ = (UniqueConstraint("booking_id", name="uq_booking_wallet_settlement_booking_id"),)

    booking_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    owner_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    walker_user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="RUB")


class WithdrawalRequest(Base):
    user_id: Mapped[PY_UUID] = mapped_column(UUID, nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    status: Mapped[WithdrawalStatus] = mapped_column(
        ENUM(WithdrawalStatus, name="withdrawal_status"),
        nullable=False,
        default=WithdrawalStatus.PENDING_MODERATION,
    )
    moderator_note: Mapped[str | None] = mapped_column(Text)
