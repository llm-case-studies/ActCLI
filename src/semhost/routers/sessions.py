from __future__ import annotations

from typing import Dict, List, Optional
import asyncio

from fastapi import APIRouter, HTTPException

from ..deps import get_status
from ..schemas.participants import BoundParams, ParticipantIn, ParticipantOut
from ..schemas.sessions import (
    RoundRecordOut,
    SessionCreate,
    SessionPatch,
    SessionSnapshot,
)
from ..services.orchestrator_service import OrchestratorRegistry, SessionWrapper, build_adapters
from ..events import get_event_bus


router = APIRouter()


_REGISTRY = OrchestratorRegistry()


@router.post("/sessions", response_model=Dict[str, str])
async def create_session_route(req: SessionCreate) -> Dict[str, str]:
    status = get_status()
    allow_cloud = status.mode == "HYBRID" and bool(status.cloud_share)

    adapters, meta = build_adapters(req.participants or [], allow_cloud=allow_cloud)
    window_k = req.window_k if req.window_k is not None else status.window_k
    wrapper = _REGISTRY.create_with_meta(
        adapters=adapters, participants_meta=meta, window_k=window_k, max_rounds=req.max_rounds
    )
    bus = get_event_bus()
    await bus.emit(wrapper.orchestrator.state.id, "session_start", {"round_idx": 0})
    return {"session_id": wrapper.orchestrator.state.id}


@router.get("/sessions", response_model=list[dict])
async def list_sessions_route() -> list[dict]:
    """Return in-memory sessions with basic metadata for picker UIs.

    Shape: [{ id, created_at, participants, round_idx }]
    """
    items: list[dict] = []
    # Best-effort: iterate over known ids (internal registry)
    try:
        for sid, wrapper in getattr(_REGISTRY, "_by_id", {}).items():
            st = wrapper.orchestrator.state
            items.append(
                {
                    "id": st.id,
                    "created_at": st.started_at,
                    "participants": list(st.participants.keys()),
                    "round_idx": st.round_idx,
                }
            )
    except Exception:
        pass
    # Newest first
    items.sort(key=lambda x: x.get("created_at", 0.0), reverse=True)
    return items


@router.get("/sessions/{session_id}", response_model=SessionSnapshot)
async def get_session_route(session_id: str) -> SessionSnapshot:
    wrapper = _REGISTRY.get(session_id)
    if wrapper is None:
        raise HTTPException(status_code=404, detail="session not found")
    return wrapper.to_snapshot()


@router.patch("/sessions/{session_id}", response_model=SessionSnapshot)
async def patch_session_route(session_id: str, patch: SessionPatch) -> SessionSnapshot:
    wrapper = _REGISTRY.get(session_id)
    if wrapper is None:
        raise HTTPException(status_code=404, detail="session not found")

    status = get_status()
    allow_cloud = status.mode == "HYBRID" and bool(status.cloud_share)

    if patch.participants is not None:
        adapters, meta = build_adapters(patch.participants, allow_cloud=allow_cloud)
        wrapper.set_participants(adapters, participants_meta=meta)

    if patch.window_k is not None:
        wrapper.orchestrator.state.window_k = int(patch.window_k)
    if patch.max_rounds is not None:
        wrapper.orchestrator.state.max_rounds = patch.max_rounds

    return wrapper.to_snapshot()


@router.post("/sessions/{session_id}/round/start", response_model=RoundRecordOut)
async def round_start_route(session_id: str, body: dict) -> RoundRecordOut:
    wrapper = _REGISTRY.get(session_id)
    if wrapper is None:
        raise HTTPException(status_code=404, detail="session not found")

    prompt = str(body.get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    focus: Optional[List[str]] = body.get("focus") or None
    seed: Optional[int] = body.get("seed")
    timeout_s: int = int(body.get("timeout_s") or 25)

    if focus:
        wrapper.orchestrator.set_focus_next(focus)

    # Ensure participants present and first round started
    if wrapper.orchestrator.state.round_idx == 0:
        wrapper.orchestrator.start()

    bus = get_event_bus()
    await bus.emit(session_id, "round_start", {"index": wrapper.orchestrator.state.round_idx, "prompt": prompt})
    rr = await asyncio.to_thread(wrapper.orchestrator.run_current_round, prompt=prompt, seed=seed, timeout_s=timeout_s)
    # Stream individual turn results
    for e in rr.entries:
        await bus.emit(
            session_id,
            "turn_result",
            {
                "index": rr.index,
                "alias": e.alias,
                "ok": e.ok,
                "latency_ms": e.latency_ms,
                "text": e.text,
                "error": e.error,
            },
        )
    await bus.emit(session_id, "round_end", {"index": rr.index})
    await bus.emit(session_id, "artifacts_saved", {"index": rr.index})
    return RoundRecordOut.from_round(rr)


@router.post("/sessions/{session_id}/round/next", response_model=RoundRecordOut)
async def round_next_route(session_id: str, body: dict | None = None) -> RoundRecordOut:
    wrapper = _REGISTRY.get(session_id)
    if wrapper is None:
        raise HTTPException(status_code=404, detail="session not found")

    prompt = str((body or {}).get("prompt") or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")
    focus: Optional[List[str]] = (body or {}).get("focus") or None
    seed: Optional[int] = (body or {}).get("seed")
    timeout_s: int = int((body or {}).get("timeout_s") or 25)

    if focus:
        wrapper.orchestrator.set_focus_next(focus)
    # Advance to next round and execute
    next_idx = wrapper.orchestrator.next_round()
    bus = get_event_bus()
    await bus.emit(session_id, "round_start", {"index": next_idx, "prompt": prompt})
    rr = await asyncio.to_thread(wrapper.orchestrator.run_current_round, prompt=prompt, seed=seed, timeout_s=timeout_s)
    for e in rr.entries:
        await bus.emit(
            session_id,
            "turn_result",
            {
                "index": rr.index,
                "alias": e.alias,
                "ok": e.ok,
                "latency_ms": e.latency_ms,
                "text": e.text,
                "error": e.error,
            },
        )
    await bus.emit(session_id, "round_end", {"index": rr.index})
    await bus.emit(session_id, "artifacts_saved", {"index": rr.index})
    return RoundRecordOut.from_round(rr)
