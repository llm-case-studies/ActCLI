from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set

from fastapi import WebSocket


@dataclass
class _Subs:
    sockets: Set[WebSocket]


class EventBus:
    """In-memory event bus keyed by session_id."""

    def __init__(self) -> None:
        self._subs: Dict[str, _Subs] = {}

    async def subscribe(self, session_id: str, ws: WebSocket) -> None:
        group = self._subs.get(session_id)
        if group is None:
            group = _Subs(sockets=set())
            self._subs[session_id] = group
        group.sockets.add(ws)

    async def unsubscribe(self, session_id: str, ws: WebSocket) -> None:
        group = self._subs.get(session_id)
        if not group:
            return
        if ws in group.sockets:
            group.sockets.remove(ws)
        if not group.sockets:
            self._subs.pop(session_id, None)

    async def emit(self, session_id: str, event_type: str, payload: dict) -> None:
        group = self._subs.get(session_id)
        if not group:
            return
        dead: Set[WebSocket] = set()
        for ws in list(group.sockets):
            try:
                await ws.send_json({
                    "type": event_type,
                    "session_id": session_id,
                    **payload,
                })
            except Exception:
                dead.add(ws)
        for ws in dead:
            await self.unsubscribe(session_id, ws)


_BUS: EventBus | None = None


def get_event_bus() -> EventBus:
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS

