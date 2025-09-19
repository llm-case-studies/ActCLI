"""
VSCode-inspired ActCLI layout with expandable left sidebar.
"""
from __future__ import annotations

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, field

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, ConditionalContainer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.filters import Condition


@dataclass
class SidebarState:
    """Track which sections are expanded."""
    logo_expanded: bool = True
    models_available_expanded: bool = True
    models_roundtable_expanded: bool = True
    colors_expanded: bool = False
    mcp_expanded: bool = False
    locations_expanded: bool = False

    # Focus management
    focused_section: Optional[str] = None
    focused_item_index: int = 0


@dataclass
class AppState:
    """Global application state."""
    models_available: List[str] = field(default_factory=lambda: ["llama3:8b", "llama3:13b", "claude-3-haiku", "gpt-4o-mini"])
    models_roundtable: List[str] = field(default_factory=lambda: ["llama3:8b", "claude-3-haiku", "gpt-4o-mini"])
    current_theme: str = "dark"
    mcp_servers: Dict[str, bool] = field(default_factory=lambda: {"git-mcp": True, "docs-mcp": False, "fs-mcp": True})
    read_locations: List[str] = field(default_factory=lambda: ["./**", "~/docs/**"])
    write_locations: List[str] = field(default_factory=lambda: ["./out/**"])


class VSCodeActCLI:
    """VSCode-inspired ActCLI interface."""

    def __init__(self, on_input: Optional[Callable[[str], str]] = None):
        self.on_input = on_input or (lambda x: f"Echo: {x}")
        self.sidebar_state = SidebarState()
        self.app_state = AppState()
        self.conversation_history = []

        # Create buffers
        self.input_buffer = Buffer(
            completer=self.create_completer(),
            complete_while_typing=True,
        )

        # Chat history buffer for selection/copy
        self.chat_buffer = Buffer(
            read_only=True,
            multiline=True,
        )

        # Create layout
        self.create_layout()
        self.create_style()
        self.create_key_bindings()

        # Create application
        self.app = Application(
            layout=self.layout,
            style=self.style,
            key_bindings=self.kb,
            full_screen=True,
            mouse_support=True,
        )

    def create_completer(self):
        """Create command completer."""
        class ActCLICompleter(Completer):
            def get_completions(self, document: Document, complete_event):
                text = document.text_before_cursor
                if text.startswith('/'):
                    commands = ['/help', '/models', '/theme', '/mcp', '/settings', '/quit']
                    for cmd in commands:
                        if cmd.startswith(text):
                            yield Completion(cmd[len(text):], start_position=0)
        return ActCLICompleter()

    def create_layout(self):
        """Create the VSCode-style layout."""

        # Left sidebar content
        sidebar_content = HSplit([
            # ASCII Art Logo
            ConditionalContainer(
                Window(
                    content=FormattedTextControl(text=self._get_logo),
                    height=lambda: 8 if self.sidebar_state.logo_expanded else 2,
                    wrap_lines=True,
                ),
                filter=Condition(lambda: True)  # Always show
            ),

            # Models Available Section
            self._create_expandable_section(
                "🤖 Models Available",
                lambda: self.sidebar_state.models_available_expanded,
                self._get_models_available,
                lambda: self._toggle_section('models_available_expanded')
            ),

            # Models in Roundtable Section
            self._create_expandable_section(
                "🎯 Roundtable",
                lambda: self.sidebar_state.models_roundtable_expanded,
                self._get_models_roundtable,
                lambda: self._toggle_section('models_roundtable_expanded')
            ),

            # Color Schemes Section
            self._create_expandable_section(
                "🎨 Themes",
                lambda: self.sidebar_state.colors_expanded,
                self._get_color_schemes,
                lambda: self._toggle_section('colors_expanded')
            ),

            # MCP Servers Section
            self._create_expandable_section(
                "🔌 MCP Servers",
                lambda: self.sidebar_state.mcp_expanded,
                self._get_mcp_servers,
                lambda: self._toggle_section('mcp_expanded')
            ),

            # Locations Section
            self._create_expandable_section(
                "📁 Locations",
                lambda: self.sidebar_state.locations_expanded,
                self._get_locations,
                lambda: self._toggle_section('locations_expanded')
            ),
        ])

        # Chat area content
        chat_content = HSplit([
            # Chat history (selectable)
            Frame(
                Window(
                    content=BufferControl(
                        buffer=self.chat_buffer,
                        focusable=True,
                    ),
                    wrap_lines=True,
                    right_margins=[ScrollbarMargin(display_arrows=True)],
                ),
                title="Chat History (Tab to focus, Ctrl+A to select all)"
            ),
            # Input area
            Frame(
                Window(
                    content=BufferControl(buffer=self.input_buffer),
                    height=3,
                    style="class:input-text",
                ),
                title="Message",
                style="class:input-frame"
            ),
            # Status bar
            Window(
                content=FormattedTextControl(text=self._get_status_bar),
                height=1,
                style="class:status-bar"
            ),
        ])

        # Main layout: sidebar | chat
        self.layout = Layout(
            VSplit([
                # Left sidebar (25%)
                Frame(
                    sidebar_content,
                    title="ActCLI",
                    style="class:sidebar-frame"
                ),
                # Chat area (75%)
                Frame(
                    chat_content,
                    title="Multi-AI Seminar",
                    style="class:chat-frame"
                ),
            ], padding=0)
        )

    def _create_expandable_section(self, title: str, is_expanded_func, content_func, toggle_func):
        """Create an expandable section."""
        return HSplit([
            # Header (clickable)
            Window(
                content=FormattedTextControl(
                    text=lambda: HTML(f'<section-header>{"▼" if is_expanded_func() else "▶"} {title}</section-header>')
                ),
                height=1,
                style="class:section-header"
            ),
            # Content (conditional)
            ConditionalContainer(
                Window(
                    content=FormattedTextControl(text=content_func),
                    wrap_lines=True,
                    style="class:section-content"
                ),
                filter=Condition(is_expanded_func)
            ),
        ])

    def _toggle_section(self, section_name: str):
        """Toggle a sidebar section."""
        current = getattr(self.sidebar_state, section_name)
        setattr(self.sidebar_state, section_name, not current)

    def _get_logo(self):
        """Get ASCII art logo."""
        if self.sidebar_state.logo_expanded:
            return HTML("""
<logo>╔═══════════════════╗
║   <title>ActCLI</title>         ║
║ <subtitle>Actuarial CLI</subtitle>   ║
║                   ║
║ <version>v0.0.1</version>  <mode>OFFLINE</mode>   ║
╚═══════════════════╝</logo>
""")
        else:
            return HTML('<logo-mini><title>ActCLI</title> <version>v0.0.1</version></logo-mini>')

    def _get_models_available(self):
        """Get available models display."""
        content = []
        is_focused = self.sidebar_state.focused_section == "models_available"

        for i, model in enumerate(self.app_state.models_available):
            status = "●" if model in self.app_state.models_roundtable else "○"

            # Highlight focused item
            if is_focused and i == self.sidebar_state.focused_item_index:
                content.append(f'<model-item-focused>▶ {status} {model}</model-item-focused>')
            else:
                content.append(f'<model-item>  {status} {model}</model-item>')

        return HTML('\n'.join(content))

    def _get_models_roundtable(self):
        """Get roundtable models display."""
        content = []
        for i, model in enumerate(self.app_state.models_roundtable, 1):
            content.append(f'<roundtable-item>{i}. <model-active>{model}</model-active></roundtable-item>')
        return HTML('\n'.join(content))

    def _get_color_schemes(self):
        """Get color schemes display."""
        themes = ["dark", "light", "nord", "solarized"]
        content = []
        for theme in themes:
            marker = "●" if theme == self.app_state.current_theme else "○"
            content.append(f'<theme-item>{marker} {theme.title()}</theme-item>')
        return HTML('\n'.join(content))

    def _get_mcp_servers(self):
        """Get MCP servers display."""
        content = []
        for server, enabled in self.app_state.mcp_servers.items():
            status = "<mcp-enabled>●</mcp-enabled>" if enabled else "<mcp-disabled>○</mcp-disabled>"
            content.append(f'<mcp-item>{status} {server}</mcp-item>')
        return HTML('\n'.join(content))

    def _get_locations(self):
        """Get locations display."""
        content = ["<location-header>Read-only:</location-header>"]
        for loc in self.app_state.read_locations:
            content.append(f'<location-read>📖 {loc}</location-read>')

        content.append("<location-header>Read-write:</location-header>")
        for loc in self.app_state.write_locations:
            content.append(f'<location-write>📝 {loc}</location-write>')

        return HTML('\n'.join(content))

    def _get_chat_content(self):
        """Get chat conversation content."""
        if not self.conversation_history:
            return HTML("""
<welcome>
<welcome-title>🤖 Welcome to ActCLI Multi-AI Seminar</welcome-title>

Ask questions about:
• <topic>Reserving strategies</topic>
• <topic>Risk modeling</topic>
• <topic>IFRS 17 calculations</topic>
• <topic>Regulatory compliance</topic>

Type your question below or use slash commands:
<command>/models</command> - Manage models
<command>/theme</command> - Change theme
<command>/help</command> - Show help
</welcome>
""")

        # Format conversation history
        content = []
        for msg in self.conversation_history[-10:]:  # Last 10 messages
            content.append(msg)
        return HTML('\n\n'.join(content))

    def _get_status_bar(self):
        """Get status bar content."""
        models_count = len(self.app_state.models_roundtable)
        return HTML(f'<status>Ready • {models_count} models active • Theme: {self.app_state.current_theme} • Press F1 for help</status>')

    def create_style(self):
        """Create the visual theme."""
        # Dynamic theme based on current selection
        if self.app_state.current_theme == "dark":
            base_bg = "#1e1e1e"
            sidebar_bg = "#252526"
            text_color = "#cccccc"
            accent = "#007acc"
            input_bg = "#3c3c3c"
            input_text = "#ffffff"
        elif self.app_state.current_theme == "light":
            base_bg = "#ffffff"
            sidebar_bg = "#f3f3f3"
            text_color = "#333333"
            accent = "#0066cc"
            input_bg = "#ffffff"
            input_text = "#000000"  # Dark text for light theme!
        else:  # nord
            base_bg = "#2e3440"
            sidebar_bg = "#3b4252"
            text_color = "#d8dee9"
            accent = "#88c0d0"
            input_bg = "#434c5e"
            input_text = "#eceff4"

        self.style = Style.from_dict({
            # Frames
            'sidebar-frame': f'bg:{sidebar_bg}',
            'chat-frame': f'bg:{base_bg}',

            # Logo
            'logo': f'{text_color}',
            'title': f'{accent} bold',
            'subtitle': f'{text_color}',
            'version': '#888888',
            'mode': '#4CAF50 bold',
            'logo-mini': f'{text_color}',

            # Sections
            'section-header': f'{accent} bold',
            'section-content': f'{text_color}',

            # Models
            'model-item': f'{text_color}',
            'model-item-focused': f'bg:{accent} {base_bg} bold',
            'model-active': f'{accent} bold',
            'roundtable-item': f'{text_color}',

            # Themes
            'theme-item': f'{text_color}',

            # MCP
            'mcp-item': f'{text_color}',
            'mcp-enabled': '#4CAF50',
            'mcp-disabled': '#888888',

            # Locations
            'location-header': f'{accent} bold',
            'location-read': '#FFC107',
            'location-write': '#4CAF50',

            # Chat
            'welcome': f'{text_color}',
            'welcome-title': f'{accent} bold',
            'topic': '#4CAF50',
            'command': f'{accent}',
            'user-msg': f'{text_color}',
            'ai-response': f'{text_color}',
            'model-response': f'{text_color}',
            'model-name': f'{accent} bold',
            'error': '#f56565',
            'help': f'{text_color}',
            'help-title': f'{accent} bold',
            'help-section': f'{accent}',
            'help-item': f'{text_color}',
            'theme-change': '#4CAF50',

            # Status
            'status-bar': f'bg:{sidebar_bg} {text_color}',
            'status': f'{text_color}',

            # Input styling
            'input-frame': f'bg:{input_bg}',
            'input-text': f'bg:{input_bg} {input_text}',
            'input-cursor': f'{input_text}',

            # General
            'frame.border': '#444444',
            'frame.title': f'{accent} bold',
        })

    def create_key_bindings(self):
        """Create keyboard shortcuts."""
        self.kb = KeyBindings()

        @self.kb.add('enter')
        def _(event):
            text = self.input_buffer.text.strip()
            if text:
                # Add user message
                user_msg = f'👤 You: {text}'
                self.conversation_history.append(f'<user-msg>{user_msg}</user-msg>')

                # Handle slash commands
                if text.startswith('/'):
                    self._handle_command(text)
                else:
                    # Get AI response
                    response = self.on_input(text)
                    ai_msg = f'🤖 Models: {response}'
                    self.conversation_history.append(f'<ai-response>{ai_msg}</ai-response>')

                # Update chat buffer for selection/copy
                self._update_chat_buffer()

                # Clear input
                self.input_buffer.text = ""

        @self.kb.add('tab')
        def _(event):
            # Tab to switch focus between input and chat history
            if event.app.layout.has_focus(self.input_buffer):
                event.app.layout.focus(self.chat_buffer)
            else:
                event.app.layout.focus(self.input_buffer)

        @self.kb.add('f1')
        def _(event):
            self._show_help()

        @self.kb.add('c-c')
        def _(event):
            event.app.exit()

        @self.kb.add('c-t')
        def _(event):
            self._cycle_theme()

        # Navigation in focused sections
        @self.kb.add('up')
        def _(event):
            if self.sidebar_state.focused_section:
                self._navigate_focused_section(-1)

        @self.kb.add('down')
        def _(event):
            if self.sidebar_state.focused_section:
                self._navigate_focused_section(1)

        @self.kb.add('space')
        def _(event):
            if self.sidebar_state.focused_section:
                self._activate_focused_item()

        @self.kb.add('escape')
        def _(event):
            # Clear focus
            self.sidebar_state.focused_section = None
            self.sidebar_state.focused_item_index = 0

    def _navigate_focused_section(self, direction: int):
        """Navigate within focused section."""
        if self.sidebar_state.focused_section == "models_available":
            max_items = len(self.app_state.models_available) - 1
            self.sidebar_state.focused_item_index = max(0, min(max_items,
                self.sidebar_state.focused_item_index + direction))

    def _activate_focused_item(self):
        """Activate the currently focused item (e.g., toggle model)."""
        if self.sidebar_state.focused_section == "models_available":
            idx = self.sidebar_state.focused_item_index
            if 0 <= idx < len(self.app_state.models_available):
                model = self.app_state.models_available[idx]
                if model in self.app_state.models_roundtable:
                    self.app_state.models_roundtable.remove(model)
                    self.conversation_history.append(f'<theme-change>➖ Removed {model} from roundtable</theme-change>')
                else:
                    self.app_state.models_roundtable.append(model)
                    self.conversation_history.append(f'<theme-change>➕ Added {model} to roundtable</theme-change>')

    def _handle_command(self, command: str):
        """Handle slash commands."""
        if command == '/help':
            self._show_help()
        elif command == '/theme':
            self._cycle_theme()
        elif command == '/models':
            # Focus on models section
            self.sidebar_state.models_available_expanded = True
            self.sidebar_state.models_roundtable_expanded = True
            self.sidebar_state.focused_section = "models_available"
            self.sidebar_state.focused_item_index = 0
            self.conversation_history.append(f'<help>🎯 Models section focused! Use ↑↓ to navigate, Space to toggle, Esc to unfocus</help>')
        elif command == '/quit':
            self.app.exit()
        else:
            self.conversation_history.append(f'<error>❌ Unknown command: {command}</error>')

    def _show_help(self):
        """Show help message."""
        help_text = """<help>
<help-title>📚 ActCLI Help</help-title>

<help-section>Slash Commands:</help-section>
<help-item>/help - Show this help</help-item>
<help-item>/models - Focus on models</help-item>
<help-item>/theme - Cycle themes</help-item>
<help-item>/quit - Exit</help-item>

<help-section>Keyboard Shortcuts:</help-section>
<help-item>F1 - Help</help-item>
<help-item>Ctrl+T - Change theme</help-item>
<help-item>Ctrl+C - Exit</help-item>
</help>"""
        self.conversation_history.append(help_text)

    def _cycle_theme(self):
        """Cycle through available themes."""
        themes = ["dark", "light", "nord"]
        current_idx = themes.index(self.app_state.current_theme)
        next_idx = (current_idx + 1) % len(themes)
        self.app_state.current_theme = themes[next_idx]

        # Recreate style with new theme
        self.create_style()
        self.app.style = self.style

        self.conversation_history.append(f'<theme-change>🎨 Theme changed to: {self.app_state.current_theme}</theme-change>')

    def _update_chat_buffer(self):
        """Update the chat buffer with plain text for selection."""
        if not self.conversation_history:
            plain_text = "Welcome to ActCLI Multi-AI Seminar\n\nAsk questions about actuarial topics..."
        else:
            # Convert HTML to plain text for selection
            plain_lines = []
            for msg in self.conversation_history[-20:]:
                # Strip HTML tags for plain text
                import re
                plain = re.sub(r'<[^>]+>', '', msg)
                plain_lines.append(plain)
            plain_text = '\n\n'.join(plain_lines)

        self.chat_buffer.text = plain_text

    def run(self):
        """Run the application."""
        # Initialize chat buffer
        self._update_chat_buffer()
        self.app.run()


def create_vscode_actcli(on_input=None):
    """Create VSCode-style ActCLI interface."""
    return VSCodeActCLI(on_input=on_input)