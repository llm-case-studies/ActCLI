from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Set, Tuple, Optional
import time

from fastapi import WebSocket
from .deps import get_settings


@dataclass
class _Subs:
    sockets: Set[WebSocket]


class EventBus:
    """In-memory event bus keyed by session_id."""

    def __init__(self) -> None:
        self._subs: Dict[str, _Subs] = {}
        self._conn_attempts: Dict[str, list[float]] = {}
        self._fail_counts: Dict[str, int] = {}
        self._tripped_until: Dict[str, float] = {}

    def allow_connect(self, session_id: str) -> Tuple[bool, Optional[str]]:
        """Rate limit websocket connections per session (sliding 60s window).

        Returns (allowed, reason_if_denied).
        """
        st = get_settings()
        limit = max(1, int(st.ws_connects_per_minute_limit))
        now = time.time()
        window = self._conn_attempts.get(session_id, [])
        window = [t for t in window if now - t < 60.0]
        if len(window) >= limit:
            self._conn_attempts[session_id] = window
            return (False, "rate limited: too many connections, try again later")
        window.append(now)
        self._conn_attempts[session_id] = window
        return (True, None)

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
        now = time.time()
        until = self._tripped_until.get(session_id)
        if until and now < until:
            return
        dead: Set[WebSocket] = set()
        for ws in list(group.sockets):
            try:
                await ws.send_json(
                    {
                        "type": event_type,
                        "session_id": session_id,
                        **payload,
                    }
                )
            except Exception:
                dead.add(ws)
                st = get_settings()
                threshold = max(1, int(st.ws_fail_threshold))
                cooldown = max(1, int(st.ws_cooldown_s))
                cnt = 1 + int(self._fail_counts.get(session_id, 0))
                if cnt >= threshold:
                    self._tripped_until[session_id] = now + float(cooldown)
                    self._fail_counts[session_id] = 0
                else:
                    self._fail_counts[session_id] = cnt
        for ws in dead:
            await self.unsubscribe(session_id, ws)


_BUS: EventBus | None = None


def get_event_bus() -> EventBus:
    global _BUS
    if _BUS is None:
        _BUS = EventBus()
    return _BUS
