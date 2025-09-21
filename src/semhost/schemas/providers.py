from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class DoctorRow(BaseModel):
    provider: Literal["codex_cli", "claude_cli"]
    binary: str
    version: str
    auth: Literal["ok", "no", "missing", "unknown"]
    hint: str


class CliLoginRequest(BaseModel):
    provider: Literal["codex_cli", "claude_cli"]


class CliLoginResponse(BaseModel):
    launched: bool
    hint: Optional[str] = None

