"""Main actcli-shell TUI application."""

import asyncio
import sys
from typing import Optional

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.formatted_text import HTML

from .session_manager import SessionManager
from .terminal_tab import TerminalManager


class Shell:
    """
    actcli-shell - Multi-terminal TUI.

    Features:
    - Tab-based terminal navigation
    - Auto-created local facilitator
    - Slash commands for control
    - Progressive complexity support
    """

    def __init__(self):
        self.session_manager = SessionManager()
        self.terminal_manager = TerminalManager()
        self.command_buffer = Buffer()
        self.output_lines = []
        self.running = False

    def get_navbar_text(self):
        """Generate navbar with terminal tabs."""
        tabs = self.terminal_manager.tabs
        if not tabs:
            return HTML("<b>No terminals</b> - Use /add to create one")

        parts = []
        for i, tab in enumerate(tabs):
            if tab.is_active:
                parts.append(f"<b>[{tab.name}]</b>")
            else:
                parts.append(f"[{tab.name}]")

        parts.append("[+]")
        return HTML(" ".join(parts))

    def get_status_text(self):
        """Generate status line."""
        session = self.session_manager.session
        if session:
            return HTML(
                f"<b>Session:</b> {session.session_id} | "
                f"<b>Facilitator:</b> {session.facilitator_url}"
            )
        return HTML("<b>No session</b>")

    def get_terminal_output(self):
        """Get output from active terminal."""
        tab = self.terminal_manager.get_active_tab()
        if not tab:
            return ""

        # Read new output
        data = tab.read_output()
        if data:
            try:
                text = data.decode('utf-8', errors='replace')
                tab.output_buffer += text
            except:
                pass

        # Return last 1000 chars
        return tab.output_buffer[-1000:]

    def create_layout(self):
        """Create the TUI layout."""
        # Status bar
        status_window = Window(
            content=FormattedTextControl(self.get_status_text),
            height=1,
        )

        # Navbar
        navbar_window = Window(
            content=FormattedTextControl(self.get_navbar_text),
            height=1,
        )

        # Terminal output area
        terminal_output = Window(
            content=FormattedTextControl(self.get_terminal_output),
            wrap_lines=True,
        )

        # Command input area
        command_input = TextArea(
            prompt="actcli-wrap>>> ",
            multiline=False,
            height=1,
        )
        self.command_input = command_input

        # Combine layout
        layout = Layout(
            HSplit([
                status_window,
                navbar_window,
                terminal_output,
                command_input,
            ])
        )

        return layout

    def create_keybindings(self):
        """Create key bindings."""
        kb = KeyBindings()

        @kb.add("c-c")
        def _(event):
            """Exit on Ctrl+C."""
            self.running = False
            event.app.exit()

        @kb.add("c-n")
        def _(event):
            """Next tab on Ctrl+N."""
            self.terminal_manager.next_tab()

        @kb.add("c-p")
        def _(event):
            """Previous tab on Ctrl+P."""
            self.terminal_manager.prev_tab()

        @kb.add("enter")
        def _(event):
            """Handle command input."""
            command = self.command_input.text.strip()
            if command:
                asyncio.create_task(self.handle_command(command))
            self.command_input.text = ""

        return kb

    async def handle_command(self, command: str):
        """Handle slash commands."""
        if command.startswith("/"):
            parts = command[1:].split()
            if not parts:
                return

            cmd = parts[0].lower()

            if cmd == "add" and len(parts) > 1:
                await self.cmd_add(parts[1:])
            elif cmd == "sessions":
                await self.cmd_sessions()
            elif cmd == "connect" and len(parts) > 1:
                await self.cmd_connect(parts[1])
            elif cmd == "help":
                await self.cmd_help()
            else:
                self.output_lines.append(f"Unknown command: {cmd}")
        else:
            # Regular input - send to active terminal
            tab = self.terminal_manager.get_active_tab()
            if tab:
                tab.write_input((command + "\n").encode())

    async def cmd_add(self, args):
        """Add a new wrapped terminal: /add <command>"""
        command = args
        name = command[0] if command else "terminal"

        tab = self.terminal_manager.add_tab(name, command)
        self.output_lines.append(f"Added terminal: {name}")

    async def cmd_sessions(self):
        """List available sessions: /sessions"""
        sessions = await self.session_manager.list_sessions()
        if sessions:
            self.output_lines.append("Available sessions:")
            for s in sessions:
                self.output_lines.append(
                    f"  {s['id']} - {s['name']} ({s['participant_count']} participants)"
                )
        else:
            self.output_lines.append("No sessions available")

    async def cmd_connect(self, session_id: str):
        """Connect to session: /connect <session_id>"""
        success = await self.session_manager.join_session(session_id, "shell")
        if success:
            self.output_lines.append(f"Connected to session: {session_id}")
        else:
            self.output_lines.append(f"Failed to connect to session: {session_id}")

    async def cmd_help(self):
        """Show help."""
        help_text = """
Available commands:
  /add <command>        - Add wrapped terminal (e.g., /add gemini)
  /sessions             - List available sessions
  /connect <id>         - Connect to session
  /help                 - Show this help

Keybindings:
  Ctrl+N - Next tab
  Ctrl+P - Previous tab
  Ctrl+C - Exit
"""
        self.output_lines.extend(help_text.strip().split("\n"))

    async def initialize(self):
        """Initialize session and facilitator."""
        self.output_lines.append("Starting local facilitator...")
        success = await self.session_manager.start_local_facilitator()

        if success:
            self.output_lines.append("✅ Facilitator started")
            self.output_lines.append("Creating default session...")

            success = await self.session_manager.create_default_session()
            if success:
                self.output_lines.append(
                    f"✅ Session created: {self.session_manager.session.session_id}"
                )
                self.output_lines.append("")
                self.output_lines.append("Type /help for commands")
                self.output_lines.append("Type /add <command> to start a terminal")
            else:
                self.output_lines.append("❌ Failed to create session")
        else:
            self.output_lines.append("❌ Failed to start facilitator")

    async def run_async(self):
        """Async run loop."""
        # Initialize
        await self.initialize()

        # Create application
        app = Application(
            layout=self.create_layout(),
            key_bindings=self.create_keybindings(),
            full_screen=True,
        )

        self.running = True

        # Run application
        try:
            await app.run_async()
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup resources."""
        self.terminal_manager.close_all()
        self.session_manager.cleanup()

    def run(self):
        """Run the shell."""
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            pass


def main():
    """
    Entry point for actcli-shell command.

    actcli-shell - Multi-terminal TUI for AI collaboration.

    Features:
    - Tab-based terminal navigation
    - Auto-created local facilitator
    - Slash commands for control
    - Real-time multi-AI conversations

    Usage:
        actcli-shell              # Launch the TUI

    Slash commands (inside TUI):
        /add <name> <cmd>        # Add new terminal
        /switch <tab>            # Switch to terminal tab
        /close                   # Close current terminal
        /quit                    # Exit application
    """
    import sys

    # Handle --help flag
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print(main.__doc__)
        return

    # Check if running in a TTY
    if not sys.stdin.isatty():
        print("Error: actcli-shell requires a TTY terminal to run.", file=sys.stderr)
        print("Please run this command in a real terminal, not in a pipe or redirect.", file=sys.stderr)
        sys.exit(1)

    shell = Shell()
    shell.run()


if __name__ == "__main__":
    main()
