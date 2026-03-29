from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.scheduled_notification import ScheduledNotification


class CRUDScheduled(CRUDBase[ScheduledNotification]):
    async def list_due(
        self,
        db: AsyncSession,
        limit: int = 200,
    ) -> list[ScheduledNotification]:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(ScheduledNotification)
            .where(
                ScheduledNotification.fire_at <= now,
                ScheduledNotification.sent_at == None,
                ScheduledNotification.deleted_at == None,
            )
            .order_by(ScheduledNotification.fire_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def cancel_for_booking(self, db: AsyncSession, booking_id: UUID) -> None:
        bid = str(booking_id)
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(ScheduledNotification).where(
                ScheduledNotification.sent_at == None,
                ScheduledNotification.deleted_at == None,
            )
        )
        for row in result.scalars():
            if (row.data or {}).get("booking_id") == bid:
                row.deleted_at = now
        await db.commit()


crud_scheduled = CRUDScheduled(ScheduledNotification)
