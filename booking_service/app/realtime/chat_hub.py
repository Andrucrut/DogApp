from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class ChatHub:
    def __init__(self) -> None:
        self._connections: dict[UUID, list[WebSocket]] = defaultdict(list)

    def register(self, conversation_id: UUID, websocket: WebSocket) -> None:
        self._connections[conversation_id].append(websocket)

    def disconnect(self, conversation_id: UUID, websocket: WebSocket) -> None:
        conns = self._connections.get(conversation_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            del self._connections[conversation_id]

    async def publish(self, conversation_id: UUID, payload: dict) -> None:
        for ws in list(self._connections.get(conversation_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(conversation_id, ws)


chat_hub = ChatHub()
