from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class WalkBroadcastHub:
    def __init__(self) -> None:
        self._connections: dict[UUID, list[WebSocket]] = defaultdict(list)

    def register(self, session_id: UUID, websocket: WebSocket) -> None:
        self._connections[session_id].append(websocket)

    def disconnect(self, session_id: UUID, websocket: WebSocket) -> None:
        conns = self._connections.get(session_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            del self._connections[session_id]

    async def publish_point(
        self,
        session_id: UUID,
        payload: dict,
    ) -> None:
        for ws in list(self._connections.get(session_id, [])):
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(session_id, ws)


walk_hub = WalkBroadcastHub()
