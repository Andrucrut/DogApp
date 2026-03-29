from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.notification import Notification


class CRUDNotification(CRUDBase[Notification]):
    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False,
    ) -> list[Notification]:
        q = select(Notification).where(
            Notification.user_id == user_id,
            Notification.deleted_at == None,
        )
        if unread_only:
            q = q.where(Notification.read_at == None)
        q = q.order_by(Notification.created_at.desc()).limit(limit).offset(offset)
        result = await db.execute(q)
        return list(result.scalars().all())


crud_notification = CRUDNotification(Notification)
