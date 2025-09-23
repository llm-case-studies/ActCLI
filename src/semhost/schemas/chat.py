from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .participants import BoundParams


class ChatOneRequest(BaseModel):
    provider: str
    model_id: Optional[str] = None
    alias: Optional[str] = None
    prompt: str
    bound_params: Optional[BoundParams] = None
    timeout_s: int = Field(default=25, ge=1)
    raw: bool = Field(default=True, description="Return raw CLI output when available (for debugging)")
    disable_tools: bool = Field(default=True, description="Best-effort: disable vendor CLI MCP/tools for speed and audit control")


class ChatOneResponse(BaseModel):
    alias: str
    model_id: str
    latency_ms: int
    ok: bool
    text: Optional[str] = None
    error: Optional[str] = None
    params_snapshot: Optional[dict] = None
