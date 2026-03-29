from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.models.payment import PaymentStatus
from app.schemas.base import BaseModel


class PaymentIntentCreate(BaseModel):
    booking_id: UUID


class PaymentRead(BaseModel):
    id: UUID
    booking_id: UUID
    payer_owner_id: UUID
    beneficiary_walker_user_id: UUID
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider: str
    external_payment_id: str | None
    failure_reason: str | None
    created_at: datetime


class MockConfirmBody(BaseModel):
    simulate_failure: bool = False
