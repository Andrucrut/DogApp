from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.walker import Walker


class CRUDWalker(CRUDBase[Walker]):

    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Walker | None:
        result = await db.execute(
            select(Walker)
            .where(Walker.user_id == user_id, Walker.deleted_at == None)
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        db: AsyncSession,
        is_available: bool = True,
        min_rating: float | None = None,
        max_price: float | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Walker]:
        query = select(Walker).where(Walker.deleted_at == None)

        if is_available:
            query = query.where(Walker.is_available == True)
        if min_rating is not None:
            query = query.where(Walker.rating >= min_rating)
        if max_price is not None:
            query = query.where(Walker.price_per_hour <= max_price)

        query = query.order_by(Walker.rating.desc()).limit(limit).offset(offset)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def update_rating(
        self, db: AsyncSession, db_obj: Walker, rating: float, reviews_count: int
    ) -> Walker:
        return await self.update(db, db_obj, {"rating": rating, "reviews_count": reviews_count})


crud_walker = CRUDWalker(Walker)