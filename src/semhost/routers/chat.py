from __future__ import annotations

from fastapi import APIRouter, HTTPException
import os

from ..deps import get_status
from ..schemas.chat import ChatOneRequest, ChatOneResponse
from ..services.orchestrator_service import build_adapters


router = APIRouter()


@router.post("/chat/one", response_model=ChatOneResponse)
async def chat_one_route(req: ChatOneRequest) -> ChatOneResponse:
    status = get_status()
    allow_cloud = status.mode == "HYBRID" and bool(status.cloud_share)

    # Build a single participant via existing builder
    from ..schemas.participants import ParticipantIn, BoundParams

    # For chat/one, the top-level timeout_s is the scheduler limit.
    # To keep semantics consistent, ignore bound_params.timeout_s so adapter-level
    # timeout doesn't override scheduler.
    bp = None
    if req.bound_params is not None:
        bp = BoundParams(**req.bound_params.model_dump())
        bp.timeout_s = None
    pi = ParticipantIn(
        alias=req.alias or req.provider,
        provider=req.provider,
        model_id=req.model_id,
        bound_params=bp,
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

    # Per-call raw/debug and tool control via env overrides (best-effort)
    prev = os.environ.get("CODEX_CLI_RAW")
    prev_dbg = os.environ.get("SEMHOST_CLI_DEBUG")
    prev_mcp = os.environ.get("ACTCLI_DISABLE_CLI_MCP")
    try:
        if req.raw:
            os.environ["CODEX_CLI_RAW"] = "1"
            os.environ["SEMHOST_CLI_DEBUG"] = "true"
        else:
            os.environ.pop("CODEX_CLI_RAW", None)
            # Leave SEMHOST_CLI_DEBUG as-is if set globally
        if req.disable_tools:
            os.environ["ACTCLI_DISABLE_CLI_MCP"] = "1"
        rr = await asyncio.to_thread(orch.run_current_round, prompt=req.prompt, seed=None, timeout_s=int(req.timeout_s))
    finally:
        if prev is None:
            os.environ.pop("CODEX_CLI_RAW", None)
        else:
            os.environ["CODEX_CLI_RAW"] = prev
        if prev_dbg is None:
            os.environ.pop("SEMHOST_CLI_DEBUG", None)
        else:
            os.environ["SEMHOST_CLI_DEBUG"] = prev_dbg
        if prev_mcp is None:
            os.environ.pop("ACTCLI_DISABLE_CLI_MCP", None)
        else:
            os.environ["ACTCLI_DISABLE_CLI_MCP"] = prev_mcp
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
