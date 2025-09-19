"""
Enhanced CLI layout system inspired by Claude CLI's design.
Creates proper input area with status space and clean visual hierarchy.
"""
from __future__ import annotations

import os
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.live import Live
from rich.layout import Layout
from rich.padding import Padding


console = Console()


class CLILayout:
    """Claude CLI-inspired layout with persistent status and clean input area."""

    def __init__(self):
        self.last_status = ""

    def create_status_header(self, mode: str, models: list[str], audit: bool = True) -> Panel:
        """Create persistent status header similar to Claude CLI."""
        status_text = Text()
        status_text.append("ActCLI", style="bold cyan")
        status_text.append(" • chat(seminar) • ", style="dim")
        status_text.append(f"MODE: {mode.upper()}", style="bright_yellow" if mode == "HYBRID" else "bright_green")
        status_text.append(" • participants: ", style="dim")
        status_text.append(", ".join(models), style="cyan")
        status_text.append(" • audit: ", style="dim")
        status_text.append("ON" if audit else "OFF", style="green" if audit else "red")

        return Panel(
            status_text,
            height=3,
            border_style="bright_black",
            padding=(0, 1)
        )

    def create_input_area(self, prompt_text: str = "actcli> ") -> Panel:
        """Create input area with proper spacing like Claude CLI."""
        input_panel = Panel(
            Padding(Text(prompt_text, style="bright_cyan"), (0, 1)),
            height=3,
            border_style="cyan",
            title="Input"
        )
        return input_panel

    def create_command_help_bar(self, commands: list[str]) -> Text:
        """Create bottom help bar with command hints."""
        help_text = Text()
        help_text.append("Commands: ", style="dim")
        help_text.append(" • ".join(commands[:4]), style="bright_black")
        help_text.append("  • /? for all", style="dim")
        return help_text

    def render_conversation_separator(self) -> None:
        """Render separator between conversation sections."""
        console.print(Rule(style="bright_black", characters="─"))
        console.print()

    def render_model_responses_grid(self, results) -> Panel:
        """Render model responses in a cleaner grid format."""
        # Create a more readable table structure
        table = Table(show_header=True, header_style="bold cyan", border_style="bright_black")
        table.add_column("Model", style="cyan", width=12)
        table.add_column("Response", style="white", overflow="fold")
        table.add_column("Time", style="dim", width=8, justify="right")

        for result in results:
            status = result.text if result.text else f"[red]{result.error or 'no output'}[/red]"
            # Truncate long responses for grid view
            if len(status) > 120:
                status = status[:117] + "..."

            table.add_row(
                result.info.name,
                status,
                f"{result.latency_ms}ms"
            )

        return Panel(
            table,
            title="Model Responses",
            border_style="cyan",
            padding=(0, 1)
        )


def print_persistent_header(mode: str, models: list[str], audit: bool = True) -> None:
    """Print the persistent header that stays visible."""
    layout = CLILayout()
    header = layout.create_status_header(mode, models, audit)
    console.print(header)


def print_input_prompt_area() -> None:
    """Print the input area that mimics Claude CLI's design."""
    # Clear visual separation with proper spacing
    console.print()
    console.print(Rule(style="bright_black"))
    console.print()

    # Status area space (reserved for status info)
    help_text = Text("Type your prompt or /help for commands", style="dim")
    console.print(Padding(help_text, (0, 2)))
    console.print()

    # Reserve space for input area (Claude CLI style)
    console.print()  # Extra space above input cursor


def enhanced_input_with_status(prompt: str = "", status_info: str = "") -> str:
    """Enhanced input function that maintains visual structure like Claude CLI."""
    try:
        # Print status if provided
        if status_info:
            console.print(f"[dim]{status_info}[/dim]")

        # Clean input without visible prompt (like Claude CLI)
        line = input("")

        # Add space below input after user presses enter (Claude CLI style)
        console.print()

        return line.strip()

    except (EOFError, KeyboardInterrupt):
        console.print("\n[dim]Exiting...[/dim]")
        raise