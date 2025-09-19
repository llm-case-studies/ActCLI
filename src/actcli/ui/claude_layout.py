"""
True Claude CLI-style layout using prompt_toolkit Application.
This implements proper terminal layout control like TypeScript CLIs.
"""
from __future__ import annotations

from typing import Optional, Callable, Any
import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.styles import Style
# Removed unused Frame import
from rich.console import Console


console = Console()


class ActCLICompleter(Completer):
    """Smart completer for ActCLI commands."""

    def __init__(self, commands: list[str]):
        self.commands = commands
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

    def get_completions(self, document: Document, complete_event):
        text = document.text_before_cursor
        if not text.startswith('/'):
            return

        for cmd in self.commands:
            if cmd.startswith(text):
                description = self.command_descriptions.get(cmd, "")
                yield Completion(
                    cmd[len(text):],
                    start_position=0,
                    display=f"{cmd} - {description}" if description else cmd
                )


class ClaudeStyleCLI:
    """Claude CLI-style terminal application with proper layout."""

    def __init__(self,
                 on_input: Optional[Callable[[str], Any]] = None,
                 get_status: Optional[Callable[[], str]] = None):
        self.on_input = on_input or (lambda x: None)
        self.get_status = get_status or (lambda: "ActCLI • MODE: OFFLINE • audit: ON")

        # Create the input buffer
        self.input_buffer = Buffer(
            completer=ActCLICompleter([
                '/help', '/?', '/models', '/models add', '/models remove',
                '/rounds', '/ollama', '/save', '/trust', '/share', '/mcp', '/quit'
            ]),
            complete_while_typing=True,
        )

        # Status display
        self.status_control = FormattedTextControl(
            text=self._get_status_text,
            focusable=False,
        )

        # Content area (for conversation history)
        self.content_control = FormattedTextControl(
            text=self._get_content_text,
            focusable=False,
        )

        # Input area
        self.input_control = BufferControl(
            buffer=self.input_buffer,
            focusable=True,
        )

        # Create layout - this is the key difference!
        self.layout = Layout(
            HSplit([
                # Header/Status bar
                Window(
                    content=self.status_control,
                    height=3,
                    style="class:status-bar",
                ),
                # Content area (conversation history)
                Window(
                    content=self.content_control,
                    wrap_lines=True,
                    right_margins=[ScrollbarMargin(display_arrows=True)],
                ),
                # Input area with space above and below
                Window(height=1),  # Space above input
                Window(
                    content=self.input_control,
                    height=1,
                    style="class:input-area",
                ),
                Window(height=2),  # Space below input for status
            ])
        )

        # Key bindings
        self.kb = KeyBindings()
        self._setup_key_bindings()

        # Style
        self.style = Style.from_dict({
            'status-bar': 'bg:#003366 #ffffff bold',
            'input-area': '#ffffff',
            'input': '#ffffff',
            'completion-menu.completion': 'bg:#003366 #ffffff',
            'completion-menu.completion.current': 'bg:#00aaaa #000000 bold',
        })

        # Create the application
        self.app = Application(
            layout=self.layout,
            key_bindings=self.kb,
            style=self.style,
            mouse_support=True,
            full_screen=True,  # This is crucial!
        )

        self.conversation_history = []

    def _setup_key_bindings(self):
        @self.kb.add('enter')
        def _(event):
            text = self.input_buffer.text.strip()
            if text:
                # Add to conversation history
                self.conversation_history.append(f"User: {text}")
                # Clear input
                self.input_buffer.text = ""
                # Call handler
                if self.on_input:
                    response = self.on_input(text)
                    if response:
                        self.conversation_history.append(f"System: {response}")

        @self.kb.add('c-c')
        def _(event):
            event.app.exit()

        @self.kb.add('c-d')
        def _(event):
            event.app.exit()

    def _get_status_text(self):
        """Get the status bar text."""
        status = self.get_status()
        return HTML(f'<status-bar>  {status}  </status-bar>')

    def _get_content_text(self):
        """Get the conversation content."""
        if not self.conversation_history:
            return HTML("""
<dim>Welcome to ActCLI Multi-AI Seminar

Type your prompt or use slash commands:
• /help - Show all commands
• /models - Manage AI models
• /quit - Exit

Start by typing a question about actuarial topics...</dim>
""")

        # Format conversation history
        formatted = []
        for line in self.conversation_history[-20:]:  # Show last 20 lines
            if line.startswith("User: "):
                formatted.append(f"<bold>❯</bold> {line[6:]}")
            elif line.startswith("System: "):
                formatted.append(f"<dim>⚡</dim> {line[8:]}")
            else:
                formatted.append(line)

        return HTML('\n'.join(formatted))

    async def run_async(self):
        """Run the application asynchronously."""
        await self.app.run_async()

    def run(self):
        """Run the application."""
        self.app.run()

    def add_message(self, message: str):
        """Add a message to the conversation history."""
        self.conversation_history.append(message)


def create_claude_style_repl(
    on_input: Optional[Callable[[str], str]] = None,
    get_status: Optional[Callable[[], str]] = None
) -> ClaudeStyleCLI:
    """Create a Claude CLI-style REPL interface."""
    return ClaudeStyleCLI(on_input=on_input, get_status=get_status)