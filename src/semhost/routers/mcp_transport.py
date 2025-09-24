from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Header, HTTPException, Request, Response
from fastapi.responses import JSONResponse, PlainTextResponse

from ..mcp.runtime import JOB_MANAGER
from ..mcp.registry import list_tools
from ..deps import get_status, update_status


router = APIRouter()


# Simple in-process session + idempotency stores (MVP)
_SESSIONS: Dict[str, Dict[str, Any]] = {}
_CALL_CACHE: Dict[str, Dict[str, Any]] = {}
_CALL_TTL_S = 300


def _now() -> int:
    return int(time.time())


def _mk_session_id() -> str:
    import secrets
    return f"sess-{secrets.token_hex(6)}"


def _touch_session(sess_id: Optional[str]) -> str:
    sid = sess_id or _mk_session_id()
    meta = _SESSIONS.get(sid) or {"created_at": _now(), "mode_lock_local": False}
    meta["touched_at"] = _now()
    _SESSIONS[sid] = meta
    return sid


def _mk_hash(payload: Any) -> str:
    s = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _prune_calls() -> None:
    cutoff = _now() - _CALL_TTL_S
    for k in list(_CALL_CACHE.keys()):
        if _CALL_CACHE[k]["ts"] < cutoff:
            _CALL_CACHE.pop(k, None)


@router.post("/mcp")
async def mcp_route(
    request: Request,
    response: Response,
    mcp_protocol_version: Optional[str] = Header(None, convert_underscores=False, alias="MCP-Protocol-Version"),
    mcp_session_id: Optional[str] = Header(None, convert_underscores=False, alias="Mcp-Session-Id"),
):
    """JSON-RPC over HTTP (streamable HTTP transport, POST /mcp).

    Supported methods (MVP): initialize, tools/list, tools/call, notifications/initialized.
    Always returns JSON (SSE is exposed via GET /mcp/sse?job=...).
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="invalid json body")

    # Normalize into a single-call JSON-RPC (MVP: no batch yet)
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="batch not supported in MVP")

    method = body.get("method")
    req_id = body.get("id")
    params = body.get("params") or {}

    # Touch/create session
    sid = _touch_session(mcp_session_id)
    # Echo protocol and session
    response.headers["Mcp-Session-Id"] = sid
    if mcp_protocol_version:
        response.headers["MCP-Protocol-Version"] = mcp_protocol_version

    def _rpc_ok(result: Dict[str, Any]) -> JSONResponse:
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "result": result})

    def _rpc_err(code: int, message: str) -> JSONResponse:
        return JSONResponse({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}, status_code=200)

    # Handle notifications-only payload
    if method == "notifications/initialized":
        return JSONResponse(status_code=202, content=None)

    if method == "initialize":
        result = {
            "protocolVersion": mcp_protocol_version or "2025-06-18",
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "ActCLI-Core-MCP", "title": "ActCLI Core MCP", "version": "0.1.0"},
            "instructions": "Tools are local-only. Use tools/call and stream via /mcp/sse?job=…",
            "session": {"id": sid, "header": "Mcp-Session-Id"},
        }
        # Surface current mode in headers for convenience
        response.headers["X-ActCLI-Mode"] = str(get_status().mode)
        return _rpc_ok(result)

    if method == "tools/list":
        tools = list_tools()
        items: List[Dict[str, Any]] = []
        for t in tools:
            items.append({
                "name": t.id,
                "title": t.title,
                "description": t.description,
                "inputSchema": t.params_schema,
            })
        return _rpc_ok({"tools": items, "nextCursor": None})

    if method == "tools/call":
        name = params.get("name") or params.get("tool")
        args = params.get("arguments") or params.get("params") or {}
        if not name:
            return _rpc_err(-32602, "Missing tool name")

        # Idempotency by request hash
        payload_fingerprint = {"name": name, "args": args}
        fp = _mk_hash(payload_fingerprint)
        _prune_calls()
        cached = _CALL_CACHE.get(fp)
        if cached:
            job_id = cached["job_id"]
        else:
            # Policy gate: if args include a RO path, flip to OFFLINE and record mode lock in session meta
            pth = str(args.get("path") or "")
            if pth.startswith("/mnt/ro/"):
                _SESSIONS[sid]["mode_lock_local"] = True
                st = get_status()
                # Move to OFFLINE if not already
                if getattr(st, "mode", None) and str(st.mode) != "OFFLINE":
                    from ..schemas.status import StatusPatch
                    update_status(StatusPatch(mode="OFFLINE", cloud_share=False))
                # Hint via header for clients
                response.headers["X-ActCLI-Mode"] = "OFFLINE"

            jr = JOB_MANAGER.create(name, args)
            job_id = jr.id
            _CALL_CACHE[fp] = {"job_id": job_id, "ts": _now()}

        # Return JSON-RPC result with job id; content + structuredContent for compatibility
        result = {
            "content": [{"type": "text", "text": f"job accepted: {job_id}"}],
            "structuredContent": {"job_id": job_id},
            "isError": False,
        }
        return _rpc_ok(result)

    return _rpc_err(-32601, f"Unknown method: {method}")


@router.get("/mcp")
def mcp_get_not_supported():
    return PlainTextResponse("SSE for unsolicited notifications not enabled; use /mcp/sse?job=…", status_code=405)
