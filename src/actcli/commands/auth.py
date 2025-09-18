from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel

from ..auth.providers import ProviderRegistry


console = Console()


def run_auth(action: str, provider: Optional[str], method: Optional[str]) -> None:
    registry = ProviderRegistry.default()
    action = action.lower()
    if action == "status":
        rows = []
        for pid, prov in registry.providers.items():
            st = prov.status()
            rows.append(f"[cyan]{pid}[/cyan]: {st}")
        console.print(Panel("\n".join(rows) or "No providers", title="Auth Status", border_style="cyan"))
        return

    if provider is None:
        console.print("Specify a provider for this action: openai|anthropic|google")
        raise SystemExit(2)

    prov = registry.get(provider)
    if prov is None:
        console.print(f"Unknown provider: {provider}")
        raise SystemExit(2)

    if action == "login":
        prov.login(preferred_method=method)
        console.print(f"Logged in to {provider} (method: {prov.method or 'unknown'})")
    elif action == "logout":
        prov.logout()
        console.print(f"Logged out of {provider}")
    else:
        console.print("Unknown action. Use: login|status|logout")
        raise SystemExit(2)

