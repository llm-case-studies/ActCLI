from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional

from platformdirs import user_config_dir

try:
    import tomllib as toml  # py311+
except Exception:  # pragma: no cover
    import tomli as toml  # type: ignore


GLOBAL_DIR = Path(user_config_dir("actcli", "actcli")) / "mcp"
GLOBAL_FILE = GLOBAL_DIR / "servers.toml"


def get_project_dir() -> Path:
    """Get the project .actcli directory based on current working directory."""
    return Path.cwd() / ".actcli"


def get_project_file() -> Path:
    """Get the project mcp.toml file path based on current working directory."""
    return get_project_dir() / "mcp.toml"


@dataclass
class MCPServer:
    name: str
    url: str
    enabled: bool = True
    group: Optional[str] = None
    desc: Optional[str] = None
    log: bool = False
    reload_url: Optional[str] = None
    restart_cmd: Optional[str] = None


@dataclass
class MCPConfig:
    servers: Dict[str, MCPServer] = field(default_factory=dict)


def _load_file(path: Path) -> Dict[str, MCPServer]:
    if not path.exists():
        return {}
    data = toml.loads(path.read_text(encoding="utf-8"))
    servers = {}
    for name, cfg in data.get("servers", {}).items():
        servers[name] = MCPServer(
            name=name,
            url=str(cfg.get("url", "")),
            enabled=bool(cfg.get("enabled", True)),
            group=cfg.get("group"),
            desc=cfg.get("desc"),
            log=bool(cfg.get("log", False)),
            reload_url=cfg.get("reload_url"),
            restart_cmd=cfg.get("restart_cmd"),
        )
    return servers


def load_mcp_config() -> MCPConfig:
    GLOBAL_DIR.mkdir(parents=True, exist_ok=True)
    get_project_dir().mkdir(parents=True, exist_ok=True)
    global_servers = _load_file(GLOBAL_FILE)
    project_servers = _load_file(get_project_file())
    merged = {**global_servers, **project_servers}
    return MCPConfig(servers=merged)


def save_project_mcp_config(cfg: MCPConfig) -> None:
    get_project_dir().mkdir(parents=True, exist_ok=True)
    # Manually write TOML to avoid requiring a writer library (tomllib has no dumps)
    lines: list[str] = []
    for name, s in cfg.servers.items():
        lines.append(f"[servers.{name}]")
        lines.append(f"url = \"{s.url}\"")
        lines.append(f"enabled = {str(bool(s.enabled)).lower()}")
        if s.group is not None:
            lines.append(f"group = \"{s.group}\"")
        if s.desc is not None:
            lines.append(f"desc = \"{s.desc}\"")
        lines.append(f"log = {str(bool(s.log)).lower()}")
        if s.reload_url is not None:
            lines.append(f"reload_url = \"{s.reload_url}\"")
        if s.restart_cmd is not None:
            lines.append(f"restart_cmd = \"{s.restart_cmd}\"")
        lines.append("")
    get_project_file().write_text("\n".join(lines), encoding="utf-8")


def get_server_by_url(cfg: MCPConfig, url: str) -> Optional[MCPServer]:
    for s in cfg.servers.values():
        if s.url.rstrip("/") == url.rstrip("/"):
            return s
    return None
