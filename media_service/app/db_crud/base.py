from typing import Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class CRUDBase(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> ModelType | None:
        result = await db.execute(
            select(self.model)
            .where(self.model.id == id, self.model.deleted_at == None)
        )
        return result.scalar_one_or_none()

    async def create(self, db: AsyncSession, obj: dict) -> ModelType:
        db_obj = self.model(**obj)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
