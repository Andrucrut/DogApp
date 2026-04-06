from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.application import BookingApplication, ApplicationStatus


class CRUDBookingApplication(CRUDBase[BookingApplication]):
    async def get_for_booking_walker(
        self,
        db: AsyncSession,
        booking_id: UUID,
        walker_id: UUID,
    ) -> BookingApplication | None:
        result = await db.execute(
            select(BookingApplication).where(
                BookingApplication.booking_id == booking_id,
                BookingApplication.walker_id == walker_id,
                BookingApplication.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_booking(
        self,
        db: AsyncSession,
        booking_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[BookingApplication]:
        result = await db.execute(
            select(BookingApplication)
            .where(
                BookingApplication.booking_id == booking_id,
                BookingApplication.deleted_at == None,
            )
            .order_by(BookingApplication.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def set_status_for_booking(
        self,
        db: AsyncSession,
        booking_id: UUID,
        accepted_walker_id: UUID,
    ) -> None:
        rows = await self.list_for_booking(db, booking_id, limit=1000, offset=0)
        for row in rows:
            if row.walker_id == accepted_walker_id:
                row.status = ApplicationStatus.ACCEPTED
            elif row.status == ApplicationStatus.PENDING:
                row.status = ApplicationStatus.REJECTED
        await db.commit()


crud_booking_application = CRUDBookingApplication(BookingApplication)
