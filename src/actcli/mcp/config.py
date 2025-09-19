from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from platformdirs import user_config_dir

try:
    import tomllib as toml  # py311+
except Exception:  # pragma: no cover
    import tomli as toml  # type: ignore


GLOBAL_DIR = Path(user_config_dir("actcli", "actcli")) / "mcp"
PROJECT_DIR = Path.cwd() / ".actcli"
GLOBAL_FILE = GLOBAL_DIR / "servers.toml"
PROJECT_FILE = PROJECT_DIR / "mcp.toml"


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
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    global_servers = _load_file(GLOBAL_FILE)
    project_servers = _load_file(PROJECT_FILE)
    merged = {**global_servers, **project_servers}
    return MCPConfig(servers=merged)


def save_project_mcp_config(cfg: MCPConfig) -> None:
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)
    # Only persist project-level servers (subset of merged)
    data = {"servers": {}}
    for name, s in cfg.servers.items():
        data["servers"][name] = {
            "url": s.url,
            "enabled": s.enabled,
            "group": s.group,
            "desc": s.desc,
            "log": s.log,
            "reload_url": s.reload_url,
            "restart_cmd": s.restart_cmd,
        }
    PROJECT_FILE.write_text(toml.dumps(data), encoding="utf-8")


def get_server_by_url(cfg: MCPConfig, url: str) -> Optional[MCPServer]:
    for s in cfg.servers.values():
        if s.url.rstrip("/") == url.rstrip("/"):
            return s
    return None

