from __future__ import annotations

from typing import List

from fastapi import APIRouter

from ..schemas.mcp import MCPServer, MCPPatch
from ..services.mcp_service import list_servers, set_enabled, get_server
from ..errors import NotFoundError


router = APIRouter()


@router.get("/mcp", response_model=list[MCPServer])
def list_mcp_route() -> List[MCPServer]:
    return list_servers()


@router.patch("/mcp/{name}", response_model=MCPServer)
def patch_mcp_route(name: str, patch: MCPPatch) -> MCPServer:
    if get_server(name) is None:
        raise NotFoundError("mcp server not found")
    return set_enabled(name, patch.enabled)
