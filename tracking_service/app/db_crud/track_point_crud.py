from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.track_point import TrackPoint


class CRUDTrackPoint(CRUDBase[TrackPoint]):
    async def list_for_session(
        self,
        db: AsyncSession,
        session_id: UUID,
        limit: int = 500,
    ) -> list[TrackPoint]:
        result = await db.execute(
            select(TrackPoint)
            .where(
                TrackPoint.session_id == session_id,
                TrackPoint.deleted_at == None,
            )
            .order_by(TrackPoint.recorded_at.asc())
            .limit(limit)
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


crud_track_point = CRUDTrackPoint(TrackPoint)
