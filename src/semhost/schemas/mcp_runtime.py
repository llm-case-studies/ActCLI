from __future__ import annotations

from typing import Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


class ToolMeta(BaseModel):
    id: str
    title: str
    profile: Literal["core", "extended", "custom"] = "core"
    params_schema: Dict[str, Any]
    description: Optional[str] = None


class RpcRequest(BaseModel):
    tool: str = Field(..., description="Tool id (e.g., excel.inspect)")
    params: Dict[str, Any] = Field(default_factory=dict)


class RpcAccepted(BaseModel):
    ok: bool = True
    job_id: str
    note: Optional[str] = None


class JobEvent(BaseModel):
    type: Literal["progress", "result", "fault"]
    pct: Optional[int] = None
    msg: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None


class CancelRequest(BaseModel):
    job_id: str


class CancelResponse(BaseModel):
    ok: bool
    job_id: str
    note: Optional[str] = None
