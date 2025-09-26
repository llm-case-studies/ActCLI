from __future__ import annotations

from typing import Dict, List, Optional
import asyncio

from fastapi import APIRouter

from ..deps import get_status
from ..schemas.sessions import (
    RoundRecordOut,
    SessionCreate,
    SessionPatch,
    SessionSnapshot,
    RoundStartRequest,
    RoundNextRequest,
)
from ..schemas.events import (
    RoundStartEvent,
    TurnResultEvent,
    RoundEndEvent,
    ArtifactsSavedEvent,
)
from ..services.orchestrator_service import OrchestratorRegistry, build_adapters
from ..events import get_event_bus
from ..services import persistence as persistence_service
from ..errors import NotFoundError, BadRequestError
from ..logging import get_logger


router = APIRouter()


_REGISTRY = OrchestratorRegistry()


@router.post("/sessions", response_model=Dict[str, str])
async def create_session_route(req: SessionCreate) -> Dict[str, str]:
    status = get_status()
    allow_cloud = status.mode == "HYBRID" and bool(status.cloud_share)

    adapters, meta = build_adapters(req.participants or [], allow_cloud=allow_cloud)
    window_k = req.window_k if req.window_k is not None else status.window_k
    wrapper = _REGISTRY.create_with_meta(
        adapters=adapters,
        participants_meta=meta,
        window_k=window_k,
        max_rounds=req.max_rounds,
    )
    bus = get_event_bus()
    await bus.emit(wrapper.orchestrator.state.id, "session_start", {"round_idx": 0})
    # Persist initial session metadata (best-effort)
    try:
        get_logger().info(
            "session_created",
            extra={
                "session_id": wrapper.orchestrator.state.id,
                "window_k": window_k,
                "max_rounds": req.max_rounds,
                "participants": len(meta),
            },
        )
        snap = wrapper.to_snapshot()
        persistence_service.upsert_session(
            session_id=snap.id,
            created_at=snap.created_at,
            window_k=snap.window_k,
            max_rounds=snap.max_rounds,
            participants=[p.model_dump() for p in snap.participants],
        )
    except Exception:
        pass
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
        raise NotFoundError("session not found")
    return wrapper.to_snapshot()


@router.patch("/sessions/{session_id}", response_model=SessionSnapshot)
async def patch_session_route(session_id: str, patch: SessionPatch) -> SessionSnapshot:
    wrapper = _REGISTRY.get(session_id)
    if wrapper is None:
        raise NotFoundError("session not found")

    status = get_status()
    allow_cloud = status.mode == "HYBRID" and bool(status.cloud_share)

    if patch.participants is not None:
        adapters, meta = build_adapters(patch.participants, allow_cloud=allow_cloud)
        wrapper.set_participants(adapters, participants_meta=meta)

    if patch.window_k is not None:
        wrapper.orchestrator.state.window_k = int(patch.window_k)
    if patch.max_rounds is not None:
        wrapper.orchestrator.state.max_rounds = patch.max_rounds
    # Persist updated session metadata (best-effort)
    try:
        get_logger().info(
            "session_patched",
            extra={
                "session_id": session_id,
                "window_k": wrapper.orchestrator.state.window_k,
                "max_rounds": wrapper.orchestrator.state.max_rounds,
            },
        )
        snap = wrapper.to_snapshot()
        persistence_service.upsert_session(
            session_id=snap.id,
            created_at=snap.created_at,
            window_k=snap.window_k,
            max_rounds=snap.max_rounds,
            participants=[p.model_dump() for p in snap.participants],
        )
    except Exception:
        pass
    return wrapper.to_snapshot()


@router.post("/sessions/{session_id}/round/start", response_model=RoundRecordOut)
async def round_start_route(session_id: str, req: RoundStartRequest) -> RoundRecordOut:
    wrapper = _REGISTRY.get(session_id)
    if wrapper is None:
        raise NotFoundError("session not found")

    prompt = req.prompt.strip()
    if not prompt:
        raise BadRequestError("prompt is required")
    focus: Optional[List[str]] = req.focus or None
    seed: Optional[int] = req.seed
    timeout_s: int = int(req.timeout_s or 25)

    if focus:
        wrapper.orchestrator.set_focus_next(focus)

    # Ensure participants present and first round started
    if wrapper.orchestrator.state.round_idx == 0:
        wrapper.orchestrator.start()

    bus = get_event_bus()
    evt_start = RoundStartEvent(
        session_id=session_id, index=wrapper.orchestrator.state.round_idx, prompt=prompt
    )
    await bus.emit(session_id, evt_start.type, evt_start.model_dump())
    get_logger().info(
        "round_start",
        extra={
            "session_id": session_id,
            "round_index": wrapper.orchestrator.state.round_idx,
            "focus": ",".join(focus or []) if focus else None,
        },
    )
    rr = await asyncio.to_thread(
        wrapper.orchestrator.run_current_round,
        prompt=prompt,
        seed=seed,
        timeout_s=timeout_s,
    )
    # Stream individual turn results
    for e in rr.entries:
        evt_turn = TurnResultEvent(
            session_id=session_id,
            index=rr.index,
            alias=e.alias,
            ok=bool(e.ok),
            latency_ms=int(e.latency_ms),
            text=getattr(e, "text", None),
            error=getattr(e, "error", None),
        )
        await bus.emit(session_id, evt_turn.type, evt_turn.model_dump())
    evt_end = RoundEndEvent(session_id=session_id, index=rr.index)
    await bus.emit(session_id, evt_end.type, evt_end.model_dump())
    evt_saved = ArtifactsSavedEvent(session_id=session_id, index=rr.index)
    await bus.emit(session_id, evt_saved.type, evt_saved.model_dump())
    # Persist round and session snapshot (best-effort)
    try:
        get_logger().info("round_end", extra={"session_id": session_id, "round_index": rr.index})
        snap = wrapper.to_snapshot()
        persistence_service.upsert_session(
            session_id=snap.id,
            created_at=snap.created_at,
            window_k=snap.window_k,
            max_rounds=snap.max_rounds,
            participants=[p.model_dump() for p in snap.participants],
        )
        rr_out = RoundRecordOut.from_round(rr)
        persistence_service.persist_round(
            session_id=snap.id,
            index=rr_out.index,
            started_at=rr_out.started_at,
            completed_at=rr_out.completed_at,
            synopsis=rr_out.synopsis,
            entries=[e.model_dump() for e in rr_out.entries],
        )
    except Exception:
        pass
    return RoundRecordOut.from_round(rr)


@router.post("/sessions/{session_id}/round/next", response_model=RoundRecordOut)
async def round_next_route(
    session_id: str, req: RoundNextRequest | None = None
) -> RoundRecordOut:
    wrapper = _REGISTRY.get(session_id)
    if wrapper is None:
        raise NotFoundError("session not found")

    prompt = (req.prompt if req else "").strip()
    if not prompt:
        raise BadRequestError("prompt is required")
    focus: Optional[List[str]] = (req.focus if req else None) or None
    seed: Optional[int] = req.seed if req else None
    timeout_s: int = int((req.timeout_s if req else 25) or 25)

    if focus:
        wrapper.orchestrator.set_focus_next(focus)
    # Advance to next round and execute
    next_idx = wrapper.orchestrator.next_round()
    bus = get_event_bus()
    evt_start = RoundStartEvent(session_id=session_id, index=next_idx, prompt=prompt)
    await bus.emit(session_id, evt_start.type, evt_start.model_dump())
    get_logger().info(
        "round_start",
        extra={
            "session_id": session_id,
            "round_index": next_idx,
            "focus": ",".join(focus or []) if focus else None,
        },
    )
    rr = await asyncio.to_thread(
        wrapper.orchestrator.run_current_round,
        prompt=prompt,
        seed=seed,
        timeout_s=timeout_s,
    )
    for e in rr.entries:
        evt_turn = TurnResultEvent(
            session_id=session_id,
            index=rr.index,
            alias=e.alias,
            ok=bool(e.ok),
            latency_ms=int(e.latency_ms),
            text=getattr(e, "text", None),
            error=getattr(e, "error", None),
        )
        await bus.emit(session_id, evt_turn.type, evt_turn.model_dump())
    evt_end = RoundEndEvent(session_id=session_id, index=rr.index)
    await bus.emit(session_id, evt_end.type, evt_end.model_dump())
    evt_saved = ArtifactsSavedEvent(session_id=session_id, index=rr.index)
    await bus.emit(session_id, evt_saved.type, evt_saved.model_dump())
    # Persist round and session snapshot (best-effort)
    try:
        get_logger().info("round_end", extra={"session_id": session_id, "round_index": rr.index})
        snap = wrapper.to_snapshot()
        persistence_service.upsert_session(
            session_id=snap.id,
            created_at=snap.created_at,
            window_k=snap.window_k,
            max_rounds=snap.max_rounds,
            participants=[p.model_dump() for p in snap.participants],
        )
        rr_out = RoundRecordOut.from_round(rr)
        persistence_service.persist_round(
            session_id=snap.id,
            index=rr_out.index,
            started_at=rr_out.started_at,
            completed_at=rr_out.completed_at,
            synopsis=rr_out.synopsis,
            entries=[e.model_dump() for e in rr_out.entries],
        )
    except Exception:
        pass
    return RoundRecordOut.from_round(rr)
