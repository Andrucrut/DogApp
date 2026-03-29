from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.schedule import Schedule


class CRUDSchedule(CRUDBase[Schedule]):
    async def list_by_walker(
        self,
        db: AsyncSession,
        walker_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Schedule]:
        result = await db.execute(
            select(Schedule)
            .where(Schedule.walker_id == walker_id, Schedule.deleted_at == None)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


crud_schedule = CRUDSchedule(Schedule)
