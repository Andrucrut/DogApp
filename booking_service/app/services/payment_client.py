from uuid import UUID

import httpx

from app.core.config import settings


async def post_wallet_settlement(booking_id: UUID) -> tuple[bool, str | None]:
    """
    Calls payment_service internal settlement. Returns (success, error_code).
    error_code: insufficient_balance, payment_unreachable, settlement_failed, ...
    """
    url = (
        f"{settings.PAYMENT_SERVICE_URL.rstrip('/')}"
        f"/api/v1/internal/settlements/bookings/{booking_id}"
    )
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
    except httpx.RequestError:
        return False, "payment_unreachable"

    if response.status_code == 200:
        return True, None
    if response.status_code == 402:
        return False, "insufficient_balance"
    try:
        detail = response.json().get("detail")
    except Exception:
        detail = None
    if isinstance(detail, str):
        return False, detail
    return False, "settlement_failed"
