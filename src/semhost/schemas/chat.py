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
    raw: bool = Field(
        default=True, description="Return raw CLI output when available (for debugging)"
    )
    disable_tools: bool = Field(
        default=True,
        description="Best-effort: disable vendor CLI MCP/tools for speed and audit control",
    )


class ChatOneResponse(BaseModel):
    alias: str
    model_id: str
    latency_ms: int
    ok: bool
    text: Optional[str] = None
    error: Optional[str] = None
    params_snapshot: Optional[dict] = None


class ChatBatchVariant(BaseModel):
    provider: str
    model_id: Optional[str] = None
    alias: Optional[str] = None
    prompt: Optional[str] = None
    bound_params: Optional[BoundParams] = None
    raw: Optional[bool] = None
    disable_tools: Optional[bool] = None
    timeout_s: Optional[int] = Field(default=None, ge=1)


class ChatBatchRequest(BaseModel):
    variants: list[ChatBatchVariant]
    prompt: Optional[str] = None
    timeout_s: int = Field(default=25, ge=1)
    concurrency: int = Field(default=1, ge=1, le=8)
    stop_on_first_ok: bool = False


class ChatBatchResponse(BaseModel):
    results: list[ChatOneResponse]
