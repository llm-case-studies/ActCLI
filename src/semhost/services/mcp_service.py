from __future__ import annotations

from typing import Dict, List, Optional

from ..schemas.mcp import MCPServer


_REGISTRY: Dict[str, MCPServer] | None = None


def _defaults() -> Dict[str, MCPServer]:
    # Lightweight curated defaults (UI placeholders; no spawn/integration here)
    defaults = [
        MCPServer(
            name="filesystem",
            url="stdio://filesystem",
            enabled=False,
            group="core",
            desc="Local FS tools",
        ),
        MCPServer(
            name="git",
            url="stdio://git",
            enabled=False,
            group="core",
            desc="Git utilities",
        ),
        MCPServer(
            name="serena",
            url="stdio://serena",
            enabled=False,
            group="examples",
            desc="Serena demo MCP",
        ),
    ]
    return {s.name: s for s in defaults}


def _ensure() -> Dict[str, MCPServer]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _defaults()
    return _REGISTRY


def list_servers() -> List[MCPServer]:
    reg = _ensure()
    return list(reg.values())


def get_server(name: str) -> Optional[MCPServer]:
    reg = _ensure()
    return reg.get(name)


def set_enabled(name: str, enabled: bool) -> MCPServer:
    reg = _ensure()
    if name not in reg:
        raise KeyError(name)
    srv = reg[name]
    reg[name] = MCPServer(**{**srv.model_dump(), "enabled": bool(enabled)})
    return reg[name]


def reset_defaults() -> None:
    global _REGISTRY
    _REGISTRY = _defaults()
