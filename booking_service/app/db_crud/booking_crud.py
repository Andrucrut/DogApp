from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.booking import Booking, BookingStatus


class CRUDBooking(CRUDBase[Booking]):
    async def list_for_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Booking]:
        result = await db.execute(
            select(Booking)
            .where(Booking.owner_id == owner_id, Booking.deleted_at == None)
            .order_by(Booking.scheduled_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_open(
        self,
        db: AsyncSession,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Booking]:
        result = await db.execute(
            select(Booking)
            .where(
                Booking.walker_id.is_(None),
                Booking.status == BookingStatus.PENDING,
                Booking.deleted_at.is_(None),
            )
            .order_by(Booking.scheduled_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_for_walker(
        self,
        db: AsyncSession,
        walker_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Booking]:
        result = await db.execute(
            select(Booking)
            .where(Booking.walker_id == walker_id, Booking.deleted_at == None)
            .order_by(Booking.scheduled_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


crud_booking = CRUDBooking(Booking)
