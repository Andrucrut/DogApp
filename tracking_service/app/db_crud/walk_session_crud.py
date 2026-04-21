from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.track_point import TrackPoint
from app.models.walk_session import WalkSession, WalkSessionStatus


class CRUDWalkSession(CRUDBase[WalkSession]):
    async def get_by_booking_id(self, db: AsyncSession, booking_id: UUID) -> WalkSession | None:
        result = await db.execute(
            select(WalkSession).where(
                WalkSession.booking_id == booking_id,
                WalkSession.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_booking_id_any(self, db: AsyncSession, booking_id: UUID) -> WalkSession | None:
        """Включая soft-deleted — нужно, чтобы не упираться в uq_walk_session_booking_id."""
        result = await db.execute(select(WalkSession).where(WalkSession.booking_id == booking_id))
        return result.scalar_one_or_none()

    async def get_live_for_booking(self, db: AsyncSession, booking_id: UUID) -> WalkSession | None:
        result = await db.execute(
            select(WalkSession).where(
                WalkSession.booking_id == booking_id,
                WalkSession.status == WalkSessionStatus.LIVE,
                WalkSession.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def hard_delete_with_points(self, db: AsyncSession, session: WalkSession) -> None:
        await db.execute(delete(TrackPoint).where(TrackPoint.session_id == session.id))
        await db.delete(session)
        await db.commit()


crud_walk_session = CRUDWalkSession(WalkSession)
