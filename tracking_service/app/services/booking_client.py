from uuid import UUID

import httpx

from app.core.config import settings


class BookingActorsInfo:
    __slots__ = ("owner_id", "walker_user_id", "status")

    def __init__(
        self,
        owner_id: UUID,
        walker_user_id: UUID | None,
        status: str,
    ) -> None:
        self.owner_id = owner_id
        self.walker_user_id = walker_user_id
        self.status = status


async def fetch_booking_actors(booking_id: UUID) -> BookingActorsInfo | None:
    url = (
        f"{settings.BOOKING_SERVICE_URL.rstrip('/')}"
        f"/api/v1/internal/bookings/{booking_id}/actors"
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
    raw_walker = data.get("walker_user_id")
    return BookingActorsInfo(
        owner_id=UUID(data["owner_id"]),
        walker_user_id=UUID(raw_walker) if raw_walker else None,
        status=data["status"],
    )
