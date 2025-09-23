from __future__ import annotations

from pydantic import BaseModel


class HistoryRow(BaseModel):
    session_id: str
    session_created_at: float
    round_index: int
    alias: str
    ok: bool
    latency_ms: int
    text_excerpt: str
    started_at: float
