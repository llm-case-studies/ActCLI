from __future__ import annotations

from fastapi import APIRouter

from actcli.version import __version__


router = APIRouter()


@router.get("/health")
def health() -> dict:
    return {"ok": True, "version": __version__}
