from datetime import datetime, timedelta, timezone
from uuid import UUID

import httpx

from app.core.config import settings


async def send_notifications(
    items: list[tuple[UUID, str, str, dict | None]],
) -> None:
    base = settings.NOTIFICATION_SERVICE_URL
    if not base or not items:
        return
    url = f"{base.rstrip('/')}/api/v1/internal/notifications"
    payload = {
        "items": [
            {
                "user_id": str(uid),
                "title": title,
                "body": body,
                "data": data or {},
            }
            for uid, title, body, data in items
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json=payload,
                headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
    except httpx.HTTPError:
        pass


async def schedule_walk_reminder(
    owner_id: UUID,
    booking_id: UUID,
    scheduled_at: datetime,
) -> None:
    base = settings.NOTIFICATION_SERVICE_URL
    if not base:
        return
    reminder_at = scheduled_at - timedelta(hours=1)
    if reminder_at <= datetime.now(timezone.utc):
        return
    url = f"{base.rstrip('/')}/api/v1/internal/scheduled-notifications"
    payload = {
        "items": [
            {
                "user_id": str(owner_id),
                "title": "Скоро прогулка",
                "body": "Через час начало забронированной прогулки.",
                "data": {
                    "booking_id": str(booking_id),
                    "event": "walk_reminder_1h",
                },
                "fire_at": reminder_at.isoformat(),
            },
        ]
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json=payload,
                headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
    except httpx.HTTPError:
        pass


async def cancel_scheduled_reminders(booking_id: UUID) -> None:
    base = settings.NOTIFICATION_SERVICE_URL
    if not base:
        return
    url = f"{base.rstrip('/')}/api/v1/internal/scheduled-notifications/cancel-by-booking"
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                url,
                json={"booking_id": str(booking_id)},
                headers={"X-Internal-Token": settings.INTERNAL_API_TOKEN},
                timeout=settings.HTTP_TIMEOUT_SECONDS,
            )
    except httpx.HTTPError:
        pass
