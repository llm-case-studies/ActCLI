from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from .participants import ParticipantIn, ParticipantOut


class EntryOut(BaseModel):
    alias: str
    model_id: str
    ok: bool
    latency_ms: int
    text: Optional[str] = None
    error: Optional[str] = None
    params_snapshot: Optional[dict] = None


class RoundRecordOut(BaseModel):
    index: int
    started_at: float
    completed_at: Optional[float] = None
    entries: List[EntryOut] = Field(default_factory=list)
    synopsis: Optional[str] = None

    @staticmethod
    def from_round(rr) -> "RoundRecordOut":
        # Import locally to avoid circulars

        if not hasattr(rr, "index"):
            raise ValueError("invalid RoundRecord")
        entries: List[EntryOut] = []
        for e in getattr(rr, "entries", []) or []:
            entries.append(
                EntryOut(
                    alias=getattr(e, "alias", ""),
                    model_id=getattr(e, "model_id", ""),
                    ok=bool(getattr(e, "ok", False)),
                    latency_ms=int(getattr(e, "latency_ms", 0)),
                    text=getattr(e, "text", None),
                    error=getattr(e, "error", None),
                    params_snapshot=getattr(e, "params_snapshot", None),
                )
            )
        return RoundRecordOut(
            index=int(getattr(rr, "index")),
            started_at=float(getattr(rr, "started_at")),
            completed_at=getattr(rr, "completed_at", None),
            entries=entries,
            synopsis=getattr(rr, "synopsis", None),
        )


class SessionCreate(BaseModel):
    participants: List[ParticipantIn] = Field(default_factory=list)
    window_k: Optional[int] = Field(default=None, ge=0)
    max_rounds: Optional[int] = Field(default=None, ge=1)
    format_id: Optional[str] = None
    cloud_share: Optional[bool] = None


class SessionPatch(BaseModel):
    participants: Optional[List[ParticipantIn]] = None
    window_k: Optional[int] = Field(default=None, ge=0)
    max_rounds: Optional[int] = Field(default=None, ge=1)


class SessionSnapshot(BaseModel):
    id: str
    created_at: float
    round_idx: int
    window_k: int
    max_rounds: Optional[int] = None
    participants: List[ParticipantOut] = Field(default_factory=list)
    history: List[RoundRecordOut] = Field(default_factory=list)


# Round request bodies
class RoundStartRequest(BaseModel):
    prompt: str
    focus: Optional[List[str]] = None
    seed: Optional[int] = None
    timeout_s: int = Field(default=25, ge=1)


class RoundNextRequest(RoundStartRequest):
    pass
