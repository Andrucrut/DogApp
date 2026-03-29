from uuid import UUID

from fastapi import APIRouter, Query, WebSocket
from jose import JWTError, jwt
from starlette.websockets import WebSocketDisconnect

from app.core.config import settings
from app.db.session import async_session_maker
from app.db_crud.walk_session_crud import crud_walk_session
from app.realtime.broadcast import walk_hub

router = APIRouter()


@router.websocket("/walk-sessions/{session_id}/stream")
async def walk_stream(
    websocket: WebSocket,
    session_id: UUID,
    token: str | None = Query(None),
) -> None:
    await websocket.accept()
    if not token:
        await websocket.close(code=1008)
        return
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        await websocket.close(code=1008)
        return
    if payload.get("type") != "access" or not payload.get("sub"):
        await websocket.close(code=1008)
        return

    user_id = UUID(payload["sub"])

    async with async_session_maker() as db:
        session = await crud_walk_session.get(db, session_id)
    if not session or session.owner_id != user_id:
        await websocket.close(code=1008)
        return

    walk_hub.register(session_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        walk_hub.disconnect(session_id, websocket)
