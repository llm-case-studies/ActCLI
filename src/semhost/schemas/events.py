from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RoundStartEvent(BaseModel):
    type: Literal["round_start"] = "round_start"
    session_id: str
    index: int = Field(..., ge=1)
    prompt: str


class TurnResultEvent(BaseModel):
    type: Literal["turn_result"] = "turn_result"
    session_id: str
    index: int = Field(..., ge=1)
    alias: str
    ok: bool
    latency_ms: int = Field(..., ge=0)
    text: Optional[str] = None
    error: Optional[str] = None


class RoundEndEvent(BaseModel):
    type: Literal["round_end"] = "round_end"
    session_id: str
    index: int = Field(..., ge=1)


class ArtifactsSavedEvent(BaseModel):
    type: Literal["artifacts_saved"] = "artifacts_saved"
    session_id: str
    index: int = Field(..., ge=1)


# Union type alias to help IDEs / imports if needed later
SessionEvent = RoundStartEvent | TurnResultEvent | RoundEndEvent | ArtifactsSavedEvent
