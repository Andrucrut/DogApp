from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.track_point import TrackPoint


class CRUDTrackPoint(CRUDBase[TrackPoint]):
    async def list_for_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        limit: int = 500,
        offset: int = 0,
    ) -> list[TrackPoint]:
        result = await db.execute(
            select(TrackPoint)
            .where(
                TrackPoint.session_id == session_id,
                TrackPoint.deleted_at == None,
            )
            .order_by(TrackPoint.recorded_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def last_for_session(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> TrackPoint | None:
        result = await db.execute(
            select(TrackPoint)
            .where(
                TrackPoint.session_id == session_id,
                TrackPoint.deleted_at == None,
            )
            .order_by(TrackPoint.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def count_for_session(
        self,
        db: AsyncSession,
        session_id: UUID,
    ) -> int:
        result = await db.execute(
            select(func.count(TrackPoint.id)).where(
                TrackPoint.session_id == session_id,
                TrackPoint.deleted_at == None,
            )
        )
        return int(result.scalar_one() or 0)


crud_track_point = CRUDTrackPoint(TrackPoint)
