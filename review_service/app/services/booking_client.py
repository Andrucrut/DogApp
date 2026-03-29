from dataclasses import dataclass
from uuid import UUID

import httpx

from app.core.config import settings


@dataclass
class ReviewContext:
    owner_id: UUID
    walker_profile_id: UUID | None
    walker_user_id: UUID | None
    status: str
    eligible: bool


async def fetch_review_context(booking_id: UUID) -> ReviewContext | None:
    url = (
        f"{settings.BOOKING_SERVICE_URL.rstrip('/')}"
        f"/api/v1/internal/bookings/{booking_id}/review-context"
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
    raw_wp = data.get("walker_profile_id")
    raw_wu = data.get("walker_user_id")
    return ReviewContext(
        owner_id=UUID(data["owner_id"]),
        walker_profile_id=UUID(raw_wp) if raw_wp else None,
        walker_user_id=UUID(raw_wu) if raw_wu else None,
        status=data["status"],
        eligible=bool(data["eligible"]),
    )


async def apply_walker_rating(walker_profile_id: UUID, rating: int) -> bool:
    url = (
        f"{settings.BOOKING_SERVICE_URL.rstrip('/')}"
        f"/api/v1/internal/walkers/{walker_profile_id}/apply-review-rating"
    )
    async with httpx.AsyncClient() as client:
        response = await client.post(
            url,
            json={"rating": rating},
            headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
            timeout=settings.HTTP_TIMEOUT_SECONDS,
        )
    return response.status_code == 200
