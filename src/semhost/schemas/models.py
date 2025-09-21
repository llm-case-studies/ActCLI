from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


AuthMechanism = Literal["local", "env", "cli", "oauth", "none"]
AuthState = Literal["ready", "missing", "signed_out", "unauthorized", "unknown"]
PolicyReason = Literal["offline", "cloud_share_disabled"]


class ModelItem(BaseModel):
    provider: str
    id: str
    source: Literal["local", "cloud(api)", "cloud(cli)"]
    # Back-compat: existing field indicating mechanism
    auth: AuthMechanism = "none"
    # New, explicit semantics
    auth_mechanism: AuthMechanism = "none"
    auth_state: Optional[AuthState] = None
    policy_allowed: bool = True
    policy_reason: Optional[PolicyReason] = None

    available: bool
    description: Optional[str] = None
    hint: Optional[str] = None
    # Back-compat alias (derived from policy/auth); will be deprecated
    blocked_reason: Optional[Literal["offline", "cloud_share_disabled", "missing_key", "cli_missing"]] = Field(
        default=None
    )
