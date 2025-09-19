from __future__ import annotations

import os
from typing import Optional

import httpx
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ..mcp.config import MCPConfig, MCPServer, load_mcp_config, save_project_mcp_config


console = Console()


def mcp_list() -> None:
    cfg = load_mcp_config()
    table = Table(title="Configured MCP servers", show_header=True, header_style="bold")
    table.add_column("Name", style="cyan")
    table.add_column("URL")
    table.add_column("Enabled")
    table.add_column("Group")
    table.add_column("Log")
    for name, s in cfg.servers.items():
        table.add_row(name, s.url, "on" if s.enabled else "off", s.group or "", "on" if s.log else "off")
    console.print(Panel(table, border_style="cyan"))


def mcp_add(name: str, url: str, group: Optional[str], desc: Optional[str]) -> None:
    cfg = load_mcp_config()
    cfg.servers[name] = MCPServer(name=name, url=url, enabled=True, group=group, desc=desc)
    save_project_mcp_config(cfg)
    console.print(Panel(f"Added MCP: {name} → {url}", border_style="green"))


def mcp_on_off(name: str, enable: bool) -> None:
    cfg = load_mcp_config()
    if name not in cfg.servers:
        console.print(f"Unknown MCP: {name}")
        raise SystemExit(2)
    cfg.servers[name].enabled = enable
    save_project_mcp_config(cfg)
    console.print(f"{name}: {'enabled' if enable else 'disabled'}")


def mcp_log(name: str, enable: bool) -> None:
    cfg = load_mcp_config()
    if name not in cfg.servers:
        console.print(f"Unknown MCP: {name}")
        raise SystemExit(2)
    cfg.servers[name].log = enable
    save_project_mcp_config(cfg)
    console.print(f"{name}: logging {'on' if enable else 'off'}")


def _probe(url: str) -> str:
    url = url.rstrip("/")
    with httpx.Client(timeout=5) as client:
        try:
            # Try health endpoint first
            r = client.get(url + "/health")
            if r.status_code == 200:
                return "healthy"
        except Exception:
            pass
        try:
            # Fall back to HEAD base
            r = client.head(url)
            return f"reachable ({r.status_code})"
        except Exception as e:
            return f"unreachable: {e}"


def mcp_test(name: str) -> None:
    cfg = load_mcp_config()
    s = cfg.servers.get(name)
    if not s:
        console.print(f"Unknown MCP: {name}")
        raise SystemExit(2)
    status = _probe(s.url)
    console.print(Panel(f"{name}: {status}", border_style=("green" if status.startswith("healthy") else "yellow")))


def mcp_reload(name: str) -> None:
    cfg = load_mcp_config()
    s = cfg.servers.get(name)
    if not s:
        console.print(f"Unknown MCP: {name}")
        raise SystemExit(2)
    if not s.reload_url:
        console.print("No reload_url configured for this MCP.")
        return
    with httpx.Client(timeout=10) as client:
        r = client.post(s.reload_url)
        if r.status_code // 100 == 2:
            console.print(Panel(f"Reload triggered for {name}", border_style="green"))
        else:
            console.print(Panel(f"Reload failed: {r.status_code} {r.text[:120]}", border_style="red"))


def mcp_restart(name: str) -> None:
    cfg = load_mcp_config()
    s = cfg.servers.get(name)
    if not s:
        console.print(f"Unknown MCP: {name}")
        raise SystemExit(2)
    if not s.restart_cmd:
        console.print("No restart_cmd configured for this MCP.")
        return
    # Fire-and-forget shell command
    os.system(s.restart_cmd)
    console.print(Panel(f"Restart command invoked for {name}", border_style="green"))

