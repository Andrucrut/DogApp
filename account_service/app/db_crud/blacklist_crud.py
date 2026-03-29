from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.blacklist import BlacklistToken


class CRUDBlacklist(CRUDBase[BlacklistToken]):

    async def add(self, db: AsyncSession, token: str) -> BlacklistToken:
        db_obj = BlacklistToken(token=token)
        db.add(db_obj)
        await db.commit()
        return db_obj

    async def is_blacklisted(self, db: AsyncSession, token: str) -> bool:
        result = await db.execute(
            select(BlacklistToken).where(BlacklistToken.token == token)
        )
        return result.scalar_one_or_none() is not None


crud_blacklist = CRUDBlacklist(BlacklistToken)