from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.payment import Payment


class CRUDPayment(CRUDBase[Payment]):
    async def get_by_booking_id(self, db: AsyncSession, booking_id: UUID) -> Payment | None:
        result = await db.execute(
            select(Payment).where(
                Payment.booking_id == booking_id,
                Payment.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Payment]:
        result = await db.execute(
            select(Payment)
            .where(
                or_(
                    Payment.payer_owner_id == user_id,
                    Payment.beneficiary_walker_user_id == user_id,
                ),
                Payment.deleted_at == None,
            )
            .order_by(Payment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


crud_payment = CRUDPayment(Payment)
