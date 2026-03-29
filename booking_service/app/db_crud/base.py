from typing import Generic, TypeVar, Type
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

    async def get_all(self, db: AsyncSession, limit: int = 100, offset: int = 0) -> list[ModelType]:
        result = await db.execute(
            select(self.model)
            .where(self.model.deleted_at == None)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj: dict) -> ModelType:
        db_obj = self.model(**obj)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: ModelType, data: dict) -> ModelType:
        for field, value in data.items():
            setattr(db_obj, field, value)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def soft_delete(self, db: AsyncSession, db_obj: ModelType) -> ModelType:
        from datetime import datetime, timezone
        db_obj.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        return db_obj