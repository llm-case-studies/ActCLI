from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..events import get_event_bus


router = APIRouter()


@router.websocket("/sessions/{session_id}/stream")
async def session_stream(session_id: str, websocket: WebSocket) -> None:
    bus = get_event_bus()
    # Simple rate limit / breaker-aware connect
    allowed, reason = bus.allow_connect(session_id)
    if not allowed:
        try:
            await websocket.close(code=1013)
        except Exception:
            pass
        return
    await websocket.accept()
    await bus.subscribe(session_id, websocket)
    try:
        # Keep the connection open; we don't consume inbound messages
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        await bus.unsubscribe(session_id, websocket)
