from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.review import Review


class CRUDReview(CRUDBase[Review]):
    async def get_by_booking_id(self, db: AsyncSession, booking_id: UUID) -> Review | None:
        result = await db.execute(
            select(Review).where(
                Review.booking_id == booking_id,
                Review.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_walker(
        self,
        db: AsyncSession,
        walker_profile_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Review]:
        result = await db.execute(
            select(Review)
            .where(
                Review.walker_profile_id == walker_profile_id,
                Review.deleted_at == None,
            )
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_by_reviewer(
        self,
        db: AsyncSession,
        reviewer_owner_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Review]:
        result = await db.execute(
            select(Review)
            .where(
                Review.reviewer_owner_id == reviewer_owner_id,
                Review.deleted_at == None,
            )
            .order_by(Review.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


crud_review = CRUDReview(Review)
