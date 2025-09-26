from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class PricingInfo(BaseModel):
    model: Literal["subscription", "per-token", "per-request", "free"]
    unit: Optional[str] = None
    input: Optional[float] = None
    output: Optional[float] = None
    currency: Optional[str] = None
    note: Optional[str] = None
    source_url: Optional[str] = None


class PricingRow(BaseModel):
    provider: str
    id: str
    pricing: PricingInfo
