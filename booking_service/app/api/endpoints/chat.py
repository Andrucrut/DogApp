from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timezone

from app.api.deps import get_current_user_id
from app.core.security import decode_token
from app.db.session import async_session_maker, get_db
from app.db_crud.chat_crud import crud_conversation, crud_message
from app.realtime.chat_hub import chat_hub
from app.schemas.chat import (
    ConversationRead,
    ConversationSummary,
    MessageCreate,
    MessagePage,
    MessageRead,
)

router = APIRouter(prefix="/conversations", tags=["chat"])


def _can_access_conversation(conversation, user_id: UUID) -> bool:
    return user_id in (conversation.owner_id, conversation.walker_user_id)


@router.get("/me", response_model=list[ConversationRead])
async def list_my_conversations(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[ConversationRead]:
    rows = await crud_conversation.list_for_user(db, user_id, limit=limit, offset=offset)
    return [ConversationRead.model_validate(r) for r in rows]


@router.get("/me/summary", response_model=list[ConversationSummary])
async def list_my_conversations_summary(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(30, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> list[ConversationSummary]:
    rows = await crud_conversation.list_for_user(db, user_id, limit=limit, offset=offset)
    out: list[ConversationSummary] = []
    for row in rows:
        last = await crud_message.last_for_conversation(db, row.id)
        unread = await crud_message.count_unread_for_user(db, row.id, user_id)
        out.append(
            ConversationSummary(
                conversation=ConversationRead.model_validate(row),
                last_message=MessageRead.model_validate(last) if last else None,
                unread_count=unread,
            )
        )
    return out


@router.get("/by-booking/{booking_id}", response_model=ConversationRead | None)
async def get_conversation_by_booking(
    booking_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> ConversationRead | None:
    conversation = await crud_conversation.get_by_booking_id(db, booking_id)
    if not conversation:
        return None
    if not _can_access_conversation(conversation, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    return ConversationRead.model_validate(conversation)


@router.get("/{conversation_id}/messages", response_model=MessagePage)
async def list_messages(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
    limit: int = Query(100, ge=1, le=500),
    cursor: UUID | None = Query(None),
) -> MessagePage:
    conversation = await crud_conversation.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if not _can_access_conversation(conversation, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    rows = await crud_message.list_for_conversation_cursor(
        db, conversation_id, limit=limit + 1, cursor_id=cursor
    )
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = items[-1].id if has_more and items else None
    return MessagePage(
        items=[MessageRead.model_validate(r) for r in items],
        next_cursor=next_cursor,
        has_more=has_more,
    )


@router.post("/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: UUID,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> MessageRead:
    conversation = await crud_conversation.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if not _can_access_conversation(conversation, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    text = body.body.strip()
    if not text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="message_empty")
    message = await crud_message.create(
        db,
        {
            "conversation_id": conversation_id,
            "sender_user_id": user_id,
            "body": text,
        },
    )
    dto = MessageRead.model_validate(message)
    await chat_hub.publish(
        conversation_id,
        {
            "type": "message",
            "conversation_id": str(conversation_id),
            "message": dto.model_dump(mode="json"),
        },
    )
    return dto


@router.post("/{conversation_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_messages_read(
    conversation_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
) -> None:
    conversation = await crud_conversation.get(db, conversation_id)
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    if not _can_access_conversation(conversation, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="forbidden")
    now = datetime.now(timezone.utc)
    await crud_message.mark_read_for_user(db, conversation_id, user_id, now)
    await chat_hub.publish(
        conversation_id,
        {
            "type": "read",
            "conversation_id": str(conversation_id),
            "reader_user_id": str(user_id),
            "read_at": now.isoformat(),
        },
    )


@router.websocket("/{conversation_id}/stream")
async def chat_stream(
    websocket: WebSocket,
    conversation_id: UUID,
    token: str | None = Query(None),
) -> None:
    await websocket.accept()
    if not token:
        await websocket.close(code=1008)
        return
    payload = decode_token(token)
    if not payload or payload.get("type") != "access" or not payload.get("sub"):
        await websocket.close(code=1008)
        return
    user_id = UUID(payload["sub"])

    async with async_session_maker() as db:
        conversation = await crud_conversation.get(db, conversation_id)
    if not conversation or not _can_access_conversation(conversation, user_id):
        await websocket.close(code=1008)
        return

    chat_hub.register(conversation_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        chat_hub.disconnect(conversation_id, websocket)
