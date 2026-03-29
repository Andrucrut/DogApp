from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.dog import Dog


class CRUDDog(CRUDBase[Dog]):
    async def list_by_owner(
        self,
        db: AsyncSession,
        owner_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Dog]:
        result = await db.execute(
            select(Dog)
            .where(Dog.owner_id == owner_id, Dog.deleted_at == None)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


crud_dog = CRUDDog(Dog)
