from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

import httpx

from app.core.config import settings


@dataclass
class PaymentContext:
    owner_id: UUID
    walker_user_id: UUID | None
    walker_profile_id: UUID | None
    status: str
    price: Decimal
    currency: str


async def fetch_payment_context(booking_id: UUID) -> PaymentContext | None:
    url = (
        f"{settings.BOOKING_SERVICE_URL.rstrip('/')}"
        f"/api/v1/internal/bookings/{booking_id}/payment-context"
    )
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
    if response.status_code != 200:
        return None
    data = response.json()
    raw_wu = data.get("walker_user_id")
    raw_wp = data.get("walker_profile_id")
    return PaymentContext(
        owner_id=UUID(data["owner_id"]),
        walker_user_id=UUID(raw_wu) if raw_wu else None,
        walker_profile_id=UUID(raw_wp) if raw_wp else None,
        status=data["status"],
        price=Decimal(data["price"]),
        currency=data.get("currency") or "RUB",
    )
