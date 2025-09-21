from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Mode(str):
    OFFLINE = "OFFLINE"
    HYBRID = "HYBRID"


class Status(BaseModel):
    mode: Literal["OFFLINE", "HYBRID"]
    cloud_share: bool
    window_k: int = Field(ge=0, default=2)
    max_rounds: Optional[int] = Field(default=None, ge=1)
    read: List[str] = Field(default_factory=list)
    write: List[str] = Field(default_factory=list)

    @field_validator("window_k")
    @classmethod
    def _validate_window_k(cls, v: int) -> int:  # type: ignore[override]
        if v < 0:
            raise ValueError("window_k must be >= 0")
        return v


class StatusPatch(BaseModel):
    mode: Optional[Literal["OFFLINE", "HYBRID"]] = None
    cloud_share: Optional[bool] = None
    window_k: Optional[int] = Field(default=None, ge=0)
    max_rounds: Optional[int] = Field(default=None, ge=1)
    read: Optional[List[str]] = None
    write: Optional[List[str]] = None

