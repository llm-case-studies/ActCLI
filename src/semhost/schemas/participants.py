from __future__ import annotations

from typing import Dict, Optional

from pydantic import BaseModel, Field


class BoundParams(BaseModel):
    seed: Optional[int] = None
    system: Optional[str] = None
    timeout_s: Optional[int] = Field(default=None, ge=1)
    temperature: Optional[float] = None


class ParticipantIn(BaseModel):
    """Incoming participant descriptor.

    Either provide `spec` (string form) or structured fields.
    """

    alias: Optional[str] = None
    spec: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None
    host: Optional[str] = None
    bound_params: Optional[BoundParams] = None


class ParticipantOut(BaseModel):
    alias: str
    provider: str
    model_id: Optional[str] = None
    bound_params: Optional[BoundParams] = None

