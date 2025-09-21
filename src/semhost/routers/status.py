from __future__ import annotations

from fastapi import APIRouter

from ..deps import get_status, update_status
from ..schemas.status import Status, StatusPatch


router = APIRouter()


@router.get("/status", response_model=Status)
def get_status_route() -> Status:
    return get_status()


@router.patch("/status", response_model=Status)
def patch_status_route(patch: StatusPatch) -> Status:
    return update_status(patch)

