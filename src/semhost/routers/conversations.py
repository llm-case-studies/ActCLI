from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query

from ..services.export_service import export_conversation
from ..settings import get_default_settings


router = APIRouter()


@router.post("/conversations/{session_id}/export")
def conversations_export_route(
    session_id: str,
    format: Literal["md", "json", "zip"] = Query(default="md"),
    compact: Literal["none", "window", "summarize"] = Query(default="none"),
    window_k: int = Query(default=2, ge=0),
    include_events: bool = Query(default=False),
) -> dict:
    try:
        st = get_default_settings()
        out_root = Path(st.output_dir)
        path = export_conversation(
            session_id,
            out_root=out_root,
            format=format,
            compact=compact,
            window_k=window_k,
            include_events=include_events,
        )
        return {"path": str(path)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
