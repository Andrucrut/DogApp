from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import Field, field_validator

from app.models.wallet import WithdrawalStatus
from app.schemas.base import BaseModel


class WalletRead(BaseModel):
    user_id: UUID
    balance: float
    currency: str


class WalletTopUpBody(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0"))

    @field_validator("amount")
    @classmethod
    def two_decimals(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class WithdrawalCreate(BaseModel):
    amount: Decimal = Field(..., gt=Decimal("0"))

    @field_validator("amount")
    @classmethod
    def two_decimals(cls, v: Decimal) -> Decimal:
        return v.quantize(Decimal("0.01"))


class WithdrawalRead(BaseModel):
    id: UUID
    user_id: UUID
    amount: float
    status: WithdrawalStatus
    moderator_note: str | None
    created_at: datetime


class SettlementRead(BaseModel):
    ok: bool
    already_settled: bool = False
    error: str | None = None
