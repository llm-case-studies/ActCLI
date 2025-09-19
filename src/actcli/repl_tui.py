from __future__ import annotations

from typing import List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from prompt_toolkit.application import get_app


class EnhancedSlashCompleter(Completer):
    """Enhanced completer that mimics Claude CLI's intelligent suggestions."""

    def __init__(self, commands: List[str]) -> None:
        # Group commands by category for better UX
        self.commands = sorted(set(commands))
        self.command_descriptions = {
            '/help': 'Show available commands',
            '/models': 'Manage AI models',
            '/models add': 'Add a new model',
            '/models remove': 'Remove a model',
            '/rounds': 'Set discussion rounds (1-3)',
            '/ollama': 'Configure Ollama host',
            '/save': 'Save transcript and audit',
            '/trust': 'Manage folder trust settings',
            '/share': 'Configure cloud sharing',
            '/mcp': 'Manage MCP servers',
            '/quit': 'Exit the application',
            '/?': 'Quick help',
        }

    def get_completions(self, document, complete_event):  # type: ignore[override]
        text = document.text_before_cursor.lower()

        # If not starting with '/', don't complete
        if not text.startswith('/'):
            return

        # Find matching commands
        for cmd in self.commands:
            if cmd.lower().startswith(text):
                # Calculate the replacement text
                completion_text = cmd[len(text):]

                # Get description for display
                description = self.command_descriptions.get(cmd, "")

                yield Completion(
                    completion_text,
                    start_position=0,
                    display=f"{cmd} - {description}" if description else cmd,
                    style="class:completion"
                )


def run_enhanced_tui_repl(commands: List[str], status_callback=None) -> Optional[str]:
    """Enhanced TUI REPL that mimics Claude CLI's polished interface.

    Returns the entered line (str) or None if user pressed Ctrl-D.
    """
    history = InMemoryHistory()
    completer = EnhancedSlashCompleter(commands)
    bindings = KeyBindings()

    # Claude CLI-inspired styling
    style = Style.from_dict({
        'completion-menu.completion': 'bg:#003366 #ffffff',
        'completion-menu.completion.current': 'bg:#00aaaa #000000 bold',
        'completion': '#888888',
        'prompt': '#00aaaa bold',
        'bottom-toolbar': 'bg:#222222 #cccccc',
        'status': 'bg:#003366 #ffffff',
    })

    @bindings.add('c-d')
    def _(event):  # type: ignore
        event.app.exit(result=None)

    @bindings.add('s-enter')  # Shift+Enter for multi-line
    def _(event):  # type: ignore
        buf = event.app.current_buffer
        buf.insert_text('\n')

    @bindings.add('tab')  # Enhanced tab completion
    def _(event):  # type: ignore
        buf = event.app.current_buffer
        if buf.complete_state:
            buf.complete_next()
        else:
            buf.start_completion()

    session = PromptSession(
        history=history,
        completer=completer,
        key_bindings=bindings,
        style=style,
        complete_style='multi-column',  # Better completion display
        mouse_support=True,
        wrap_lines=True,
    )

    try:
        # Create Claude CLI-style clean prompt (no visible prompt text)
        prompt_text = HTML('')

        # Status-aware bottom toolbar
        if status_callback:
            toolbar_text = status_callback()
        else:
            toolbar_text = "Type /help for commands • Ctrl+D to quit • Tab for completions"

        bottom_bar = HTML(f'<bottom-toolbar>{toolbar_text}</bottom-toolbar>')

        line = session.prompt(
            prompt_text,
            bottom_toolbar=bottom_bar,
            placeholder=HTML('<class:placeholder>Enter a prompt or /command...</class:placeholder>')
        )
        return line.strip()

    except (EOFError, KeyboardInterrupt):
        return None


def run_tui_input_loop(commands: List[str], *, toolbar: str = "") -> Optional[str]:
    """Legacy function for backward compatibility."""
    return run_enhanced_tui_repl(commands, lambda: toolbar)

