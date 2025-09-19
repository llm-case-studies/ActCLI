from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Tuple

import readchar
from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table


console = Console()


def _normalize(options: Sequence[Tuple[str, str]] | Sequence[str]) -> List[Tuple[str, str]]:
    norm: List[Tuple[str, str]] = []
    if not options:
        return norm
    if isinstance(options[0], tuple):  # type: ignore[index]
        norm = [(str(k), str(v)) for k, v in options]  # type: ignore[arg-type]
    else:
        norm = [(str(x), "") for x in options]  # type: ignore[list-item]
    return norm


def select_one(options: Sequence[Tuple[str, str]] | Sequence[str], *, title: str = "Select", help_text: str = "↑/↓ to navigate • Enter to select • Esc to cancel") -> Optional[str]:
    items = _normalize(options)
    if not items:
        return None
    idx = 0

    def _render() -> Panel:
        table = Table.grid(padding=(0, 2))
        for i, (left, right) in enumerate(items):
            prefix = "▶" if i == idx else " "
            left_text = f"[bright_cyan]{left}[/bright_cyan]" if i == idx else left
            if right:
                table.add_row(prefix, left_text, right)
            else:
                table.add_row(prefix, left_text)
        table.add_row("", f"[dim]{help_text}[/dim]")
        return Panel(table, title=title, border_style="cyan", padding=(0, 1))

    with Live(_render(), console=console, transient=True, refresh_per_second=30) as live:
        while True:
            key = readchar.readkey()
            if key in (readchar.key.CTRL_C, readchar.key.ESC):
                return None
            if key == readchar.key.UP:
                idx = (idx - 1) % len(items)
                live.update(_render())
                continue
            if key == readchar.key.DOWN:
                idx = (idx + 1) % len(items)
                live.update(_render())
                continue
            if key in (readchar.key.ENTER, "\r", "\n"):
                return items[idx][0]

    return None

