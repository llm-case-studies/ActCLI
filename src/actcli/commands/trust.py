from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel

from ..trust import get_trust, set_trust, revoke_trust


console = Console()


def run_trust(action: str, scope: Optional[str], cloud_share: Optional[bool]) -> None:
    action = action.lower()
    if action == "status":
        tr = get_trust()
        if not tr:
            console.print(Panel("Untrusted. Use 'actcli trust allow-here' to trust this folder.", title="Trust", border_style="yellow"))
        else:
            lines = [f"path: {tr.path}", f"scope: {tr.scope}", f"read: {', '.join(tr.read)}", f"write: {', '.join(tr.write)}", f"cloud_share: {tr.cloud_share}"]
            console.print(Panel("\n".join(lines), title="Trust", border_style="green"))
        return
    if action in ("allow-here", "allow-once"):
        scope_val = "persist" if action == "allow-here" else "once"
        read = ["./**"]
        write = ["./out/**"]
        cs = bool(cloud_share) if cloud_share is not None else False
        set_trust(None, scope_val, read, write, cs)
        console.print(Panel(f"Trusted this folder (scope={scope_val}, cloud_share={cs}).", border_style="green"))
        return
    if action == "revoke":
        revoke_trust()
        console.print(Panel("Trust revoked for this folder.", border_style="yellow"))
        return
    console.print("Unknown action. Use: status|allow-here|allow-once|revoke")

