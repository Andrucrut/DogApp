from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.wallet import Wallet, WithdrawalRequest, WithdrawalStatus


class CRUDWallet(CRUDBase[Wallet]):
    async def get_by_user_id(self, db: AsyncSession, user_id: UUID) -> Wallet | None:
        result = await db.execute(
            select(Wallet).where(
                Wallet.user_id == user_id,
                Wallet.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def ensure_wallet(self, db: AsyncSession, user_id: UUID) -> Wallet:
        w = await self.get_by_user_id(db, user_id)
        if w:
            return w
        w = Wallet(user_id=user_id, balance=Decimal("0.00"))
        db.add(w)
        await db.flush()
        await db.refresh(w)
        return w


class CRUDWithdrawal(CRUDBase[WithdrawalRequest]):
    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[WithdrawalRequest]:
        result = await db.execute(
            select(WithdrawalRequest)
            .where(
                WithdrawalRequest.user_id == user_id,
                WithdrawalRequest.deleted_at == None,
            )
            .order_by(WithdrawalRequest.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


crud_wallet = CRUDWallet(Wallet)
crud_withdrawal = CRUDWithdrawal(WithdrawalRequest)

__all__ = ["crud_wallet", "crud_withdrawal", "WithdrawalStatus"]
