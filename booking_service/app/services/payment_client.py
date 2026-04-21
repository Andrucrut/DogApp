from uuid import UUID

import httpx

from app.core.config import settings


def _candidate_settlement_urls(booking_id: UUID) -> list[str]:
    base = settings.PAYMENT_SERVICE_URL.rstrip("/")
    suffix = f"/internal/settlements/bookings/{booking_id}"
    if base.endswith("/api/v1"):
        return [f"{base}{suffix}"]
    return [
        f"{base}/api/v1{suffix}",
        # Фолбэк для конфигураций, где base указывает на API Gateway корень.
        f"{base}/payment/api/v1{suffix}",
    ]


async def post_wallet_settlement(booking_id: UUID) -> tuple[bool, str | None]:
    """
    Calls payment_service internal settlement. Returns (success, error_code).
    error_code: insufficient_balance, payment_unreachable, settlement_failed, ...
    """
    response = None
    async with httpx.AsyncClient() as client:
        for url in _candidate_settlement_urls(booking_id):
            try:
                response = await client.post(
                    url,
                    headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
                    timeout=settings.HTTP_TIMEOUT_SECONDS,
                )
                break
            except httpx.RequestError:
                continue
    if response is None:
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
