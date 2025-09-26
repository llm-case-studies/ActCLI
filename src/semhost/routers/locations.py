from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter

from ..deps import get_status, update_status
from ..schemas.status import StatusPatch


router = APIRouter()


@router.get("/locations", response_model=Dict[str, List[str]])
def get_locations_route() -> Dict[str, List[str]]:
    st = get_status()
    return {"read": list(st.read or []), "write": list(st.write or [])}


@router.patch("/locations", response_model=Dict[str, List[str]])
def patch_locations_route(body: Dict[str, List[str]]) -> Dict[str, List[str]]:
    read = body.get("read")
    write = body.get("write")
    patch = StatusPatch(read=read, write=write)
    st = update_status(patch)
    return {"read": list(st.read or []), "write": list(st.write or [])}
