from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db_crud.base import CRUDBase
from app.models.chat import Conversation, Message


class CRUDConversation(CRUDBase[Conversation]):
    async def get_by_booking_id(
        self,
        db: AsyncSession,
        booking_id: UUID,
    ) -> Conversation | None:
        result = await db.execute(
            select(Conversation).where(
                Conversation.booking_id == booking_id,
                Conversation.deleted_at == None,
            )
        )
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Conversation]:
        result = await db.execute(
            select(Conversation)
            .where(
                Conversation.deleted_at == None,
                (Conversation.owner_id == user_id) | (Conversation.walker_user_id == user_id),
            )
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


class CRUDMessage(CRUDBase[Message]):
    async def list_for_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Message]:
        result = await db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.deleted_at == None,
            )
            .order_by(Message.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def list_for_conversation_cursor(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        limit: int = 100,
        cursor_id: UUID | None = None,
    ) -> list[Message]:
        query = (
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.deleted_at == None,
            )
            .order_by(Message.id.asc())
            .limit(limit)
        )
        if cursor_id:
            query = query.where(Message.id > cursor_id)
        result = await db.execute(query)
        return list(result.scalars().all())

    async def count_unread_for_user(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
    ) -> int:
        result = await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation_id,
                Message.deleted_at == None,
                Message.sender_user_id != user_id,
                Message.read_at.is_(None),
            )
        )
        return int(result.scalar_one() or 0)

    async def last_for_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID,
    ) -> Message | None:
        result = await db.execute(
            select(Message)
            .where(
                Message.conversation_id == conversation_id,
                Message.deleted_at == None,
            )
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def mark_read_for_user(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        read_at,
    ) -> int:
        rows = await self.list_for_conversation(db, conversation_id, limit=1000, offset=0)
        updated = 0
        for row in rows:
            if row.sender_user_id != user_id and row.read_at is None:
                row.read_at = read_at
                updated += 1
        await db.commit()
        return updated


crud_conversation = CRUDConversation(Conversation)
crud_message = CRUDMessage(Message)
