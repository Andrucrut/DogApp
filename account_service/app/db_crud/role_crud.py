from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.role import Role


class CRUDRole(CRUDBase[Role]):

    async def get_by_key(self, db: AsyncSession, key: str) -> Role | None:
        result = await db.execute(select(Role).where(Role.key == key))
        return result.scalar_one_or_none()


crud_role = CRUDRole(Role)