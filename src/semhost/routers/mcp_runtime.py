from __future__ import annotations

from typing import List
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import json
import time

from ..mcp.registry import list_tools
from ..mcp.runtime import JOB_MANAGER
from ..schemas.mcp_runtime import (
    ToolMeta,
    RpcRequest,
    RpcAccepted,
    CancelRequest,
    CancelResponse,
)


router = APIRouter()


@router.get("/mcp/tools", response_model=List[ToolMeta])
def mcp_tools_route() -> List[ToolMeta]:
    return list_tools()


@router.post("/mcp/rpc", response_model=RpcAccepted)
def mcp_rpc_route(req: RpcRequest) -> RpcAccepted:
    # MVP: accept job and return id; streaming handled by /mcp/sse
    jr = JOB_MANAGER.create(req.tool, req.params)
    return RpcAccepted(
        ok=True,
        job_id=jr.id,
        note="MVP: worker not yet implemented; use /mcp/sse for stub stream",
    )


@router.get("/mcp/sse")
def mcp_sse_route(job: str):
    # MVP: stream a short canned sequence so UI wiring can be tested.
    def _gen():
        from ..tools.excel.inspect import stream as excel_stream
        from ..tools.web_bridge import stream as bridge_stream

        last_ping = time.time()
        jr = JOB_MANAGER.get(job)
        if jr is None:
            fault = {"event": "fault", "job": job, "ok": False, "error": "unknown job"}
            yield f"data: {json.dumps(fault)}\n\n"
            return
        # Route to tool-specific stream
        if jr.tool == "excel.inspect":
            for ev in excel_stream(job, jr.params):
                yield f"data: {json.dumps(ev)}\n\n"
                # heartbeat while streaming
                if time.time() - last_ping > 10:
                    yield ": ping\n\n"
                    last_ping = time.time()
        elif jr.tool in ("participants.register", "participants.message", "events.log"):
            params = dict(jr.params)
            params["__tool_id"] = jr.tool
            for ev in bridge_stream(job, params):
                yield f"data: {json.dumps(ev)}\n\n"
                if time.time() - last_ping > 10:
                    yield ": ping\n\n"
                    last_ping = time.time()
        else:
            fault = {
                "event": "fault",
                "job": job,
                "ok": False,
                "error": f"unsupported tool: {jr.tool}",
            }
            yield f"data: {json.dumps(fault)}\n\n"

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(_gen(), media_type="text/event-stream", headers=headers)


@router.post("/mcp/cancel", response_model=CancelResponse)
def mcp_cancel_route(req: CancelRequest) -> CancelResponse:
    ok = JOB_MANAGER.cancel(req.job_id)
    return CancelResponse(ok=ok, job_id=req.job_id, note=None if ok else "unknown job")
