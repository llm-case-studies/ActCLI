from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class DoctorRow(BaseModel):
    provider: Literal["codex_cli", "claude_cli", "gemini_cli"]
    binary: str
    version: str
    auth: Literal["ok", "no", "missing", "unknown"]
    hint: str


class CliLoginRequest(BaseModel):
    provider: Literal["codex_cli", "claude_cli", "gemini_cli"]


class CliLoginResponse(BaseModel):
    launched: bool
    hint: Optional[str] = None


class CliModelSwitchRequest(BaseModel):
    provider: Literal["codex_cli", "gemini_cli", "claude_cli"]
    model: str


class CliModelSwitchResponse(BaseModel):
    ok: bool
    hint: Optional[str] = None
