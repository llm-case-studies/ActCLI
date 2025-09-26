from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class MCPServer(BaseModel):
    name: str
    url: str
    enabled: bool = False
    group: Optional[str] = None
    desc: Optional[str] = None


class MCPPatch(BaseModel):
    enabled: bool = Field(..., description="Enable or disable this MCP server")
