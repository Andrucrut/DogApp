from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.user import User
from app.models.base import UserStatus


class CRUDUser(CRUDBase[User]):

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_phone(self, db: AsyncSession, phone: str) -> User | None:
        result = await db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def get_by_email_or_phone(
        self, db: AsyncSession, email: str | None = None, phone: str | None = None
    ) -> User | None:
        if email:
            return await self.get_by_email(db, email)
        if phone:
            return await self.get_by_phone(db, phone)
        return None

    async def block(self, db: AsyncSession, db_obj: User) -> User:
        db_obj.status = UserStatus.BLOCKED
        db_obj.is_active = False
        await db.commit()
        return db_obj

    async def delete(self, db: AsyncSession, db_obj: User) -> User:
        db_obj.status = UserStatus.DELETED
        db_obj.is_active = False
        return await self.soft_delete(db, db_obj)


crud_user = CRUDUser(User)