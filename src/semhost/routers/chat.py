from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..deps import get_status
from ..schemas.chat import ChatOneRequest, ChatOneResponse
from ..services.orchestrator_service import build_adapters


router = APIRouter()


@router.post("/chat/one", response_model=ChatOneResponse)
async def chat_one_route(req: ChatOneRequest) -> ChatOneResponse:
    status = get_status()
    allow_cloud = status.mode == "HYBRID" and bool(status.cloud_share)

    # Build a single participant via existing builder
    from ..schemas.participants import ParticipantIn

    pi = ParticipantIn(
        alias=req.alias or req.provider,
        provider=req.provider,
        model_id=req.model_id,
        bound_params=req.bound_params,
    )
    adapters, _meta = build_adapters([pi], allow_cloud=allow_cloud)
    if not adapters:
        raise HTTPException(status_code=400, detail="no adapter available for given provider/model")

    # Run a one-off round
    from actcli.seminar.rounds import RoundOrchestrator

    orch = RoundOrchestrator(window_k=0, max_rounds=1)
    orch.set_participants(adapters)
    orch.start()

    # Use run in thread pool (async safe)
    import asyncio

    rr = await asyncio.to_thread(orch.run_current_round, prompt=req.prompt, seed=None, timeout_s=int(req.timeout_s))
    if not rr.entries:
        raise HTTPException(status_code=500, detail="no entries returned")
    e = rr.entries[0]
    return ChatOneResponse(
        alias=e.alias,
        model_id=e.model_id,
        latency_ms=e.latency_ms,
        ok=e.ok,
        text=e.text,
        error=e.error,
        params_snapshot=e.params_snapshot,
    )

