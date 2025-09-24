from __future__ import annotations

from typing import List

from fastapi import APIRouter, Query

from ..deps import get_settings, get_status
from ..schemas.models import ModelItem
from ..services.model_aggregator import aggregate_models


router = APIRouter()


@router.get("/models", response_model=list[ModelItem])
def list_models_route(
    refresh: bool = Query(default=False, description="Force refresh from providers (bypass cache)"),
    strict: bool = Query(default=False, description="For CLI providers, show only discovered models (no fallbacks)"),
) -> List[ModelItem]:
    settings = get_settings()
    status = get_status()
    return aggregate_models(settings, status, refresh=refresh, strict_cli=strict)
