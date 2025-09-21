from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class ModelItem(BaseModel):
    provider: str
    id: str
    source: Literal["local", "cloud(api)", "cloud(cli)"]
    auth: Literal["local", "env", "cli", "none"]
    available: bool
    description: Optional[str] = None
    blocked_reason: Optional[Literal["offline", "cloud_share_disabled", "missing_key", "cli_missing"]] = Field(
        default=None
    )

