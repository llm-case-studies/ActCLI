from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..schemas.pricing import PricingRow
from ..services.pricing_service import pricing_catalog


router = APIRouter()


@router.get("/pricing", response_model=list[PricingRow])
def get_pricing_route() -> List[PricingRow]:
    return pricing_catalog()

