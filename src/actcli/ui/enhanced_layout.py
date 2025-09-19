"""
Enhanced ActCLI layout examples showing advanced prompt_toolkit capabilities.
"""
from __future__ import annotations

from typing import Optional
from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, WindowAlign
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import Frame, Box
from prompt_toolkit.formatted_text import HTML


class AdvancedActCLILayout:
    """Showcase of advanced layout capabilities."""

    def __init__(self):
        # Create different content sections
        self.create_buffers()
        self.create_layout()
        self.create_style()

    def create_buffers(self):
        """Create different content buffers."""
        self.chat_buffer = Buffer(multiline=True, scrollbar=True)
        self.models_buffer = Buffer(multiline=True)
        self.logs_buffer = Buffer(multiline=True)

    def create_layout(self):
        """Create advanced multi-section layout."""

        # Header bar
        header = Window(
            content=FormattedTextControl(
                text=HTML('<header>🤖 ActCLI Multi-AI Seminar • MODE: <mode>OFFLINE</mode> • Models: <models>3 active</models></header>')
            ),
            height=1,
            style="class:header"
        )

        # Left sidebar - Model status
        model_status = Frame(
            Window(
                content=FormattedTextControl(
                    text=self._get_model_status
                ),
                wrap_lines=True,
            ),
            title="Models",
            style="class:sidebar"
        )

        # Main chat area
        chat_area = Frame(
            Window(
                content=BufferControl(buffer=self.chat_buffer),
                wrap_lines=True,
                scrollbar=True,
            ),
            title="Conversation",
            style="class:main"
        )

        # Right sidebar - Logs/Debug
        logs_area = Frame(
            Window(
                content=FormattedTextControl(
                    text=self._get_logs
                ),
                wrap_lines=True,
                scrollbar=True,
            ),
            title="System Logs",
            style="class:logs"
        )

        # Input area
        input_area = Frame(
            Window(
                content=FormattedTextControl(
                    text=HTML('<input>Type your message...</input>')
                ),
                height=3,
            ),
            title="Input",
            style="class:input"
        )

        # Status bar
        status_bar = Window(
            content=FormattedTextControl(
                text=HTML('<status>Ready • Press Tab for completion • /help for commands</status>')
            ),
            height=1,
            style="class:status"
        )

        # Combine into sophisticated layout
        self.layout = Layout(
            HSplit([
                header,
                VSplit([
                    # Left column (25% width)
                    Box(
                        body=model_status,
                        style="class:left-pane",
                        width=25
                    ),
                    # Middle column (50% width)
                    Box(
                        body=HSplit([
                            chat_area,
                            input_area,
                        ]),
                        style="class:center-pane",
                        width=50
                    ),
                    # Right column (25% width)
                    Box(
                        body=logs_area,
                        style="class:right-pane",
                        width=25
                    ),
                ], padding=1),
                status_bar,
            ])
        )

    def _get_model_status(self):
        """Dynamic model status display."""
        return HTML("""
<model-llama>🦙 LLaMA 3.1</model-llama>
<status-online>● Online</status-online> 420ms

<model-claude>🤖 Claude 3.5</model-claude>
<status-online>● Online</status-online> 280ms

<model-gpt>🧠 GPT-4</model-gpt>
<status-offline>● Offline</status-offline> Rate limit

<divider>──────────────</divider>

<setting>Rounds:</setting> 2
<setting>Timeout:</setting> 25s
<setting>Mode:</setting> Offline
""")

    def _get_logs(self):
        """Dynamic logs display."""
        return HTML("""
<log-info>[14:10:19]</log-info> Starting seminar
<log-success>[14:10:20]</log-success> LLaMA connected
<log-success>[14:10:21]</log-success> Claude connected
<log-warning>[14:10:22]</log-warning> GPT rate limited
<log-info>[14:10:23]</log-info> Ready for input
""")

    def create_style(self):
        """Create rich color scheme."""
        self.style = Style.from_dict({
            # Header styling
            'header': 'bg:#2d3748 #ffffff bold',
            'mode': '#48bb78 bold',
            'models': '#4299e1 bold',

            # Panel styling
            'sidebar': 'bg:#1a202c',
            'main': 'bg:#2d3748',
            'logs': 'bg:#1a202c',
            'input': 'bg:#4a5568',

            # Pane styling
            'left-pane': 'bg:#1a202c',
            'center-pane': 'bg:#2d3748',
            'right-pane': 'bg:#1a202c',

            # Model status
            'model-llama': 'bg:#ff6b6b #ffffff bold',
            'model-claude': 'bg:#4ecdc4 #000000 bold',
            'model-gpt': 'bg:#45b7d1 #ffffff bold',
            'status-online': '#48bb78 bold',
            'status-offline': '#f56565 bold',
            'setting': '#a0aec0',
            'divider': '#4a5568',

            # Logs
            'log-info': '#a0aec0',
            'log-success': '#48bb78',
            'log-warning': '#ed8936',
            'log-error': '#f56565',

            # Status bar
            'status': 'bg:#1a202c #a0aec0',

            # Input
            'input': '#e2e8f0',

            # Frame borders
            'frame.border': '#4a5568',
            'frame.title': '#e2e8f0 bold',
        })

    def create_app(self):
        """Create the full application."""
        return Application(
            layout=self.layout,
            style=self.style,
            full_screen=True,
            mouse_support=True,
        )


def create_tabbed_layout():
    """Example of tabbed interface."""
    from prompt_toolkit.layout.containers import HSplit
    from prompt_toolkit.widgets import Frame

    # Simple tab simulation using frames
    tabs = HSplit([
        Window(
            content=FormattedTextControl(
                text=HTML('<tabs>[Chat] [Models] [Settings] [Logs]</tabs>')
            ),
            height=1,
            style="class:tabs"
        ),
        Frame(
            Window(
                content=FormattedTextControl(
                    text=HTML('<tab-content>Current tab content goes here...</tab-content>')
                ),
                wrap_lines=True,
            ),
            title="Active Tab",
        )
    ])

    return Layout(tabs)


def create_dashboard_layout():
    """Example of dashboard-style layout."""

    # Create grid of information panels
    top_row = VSplit([
        Frame(Window(FormattedTextControl(text=HTML('<metric>Models: <value>3</value></metric>'))), title="Active Models"),
        Frame(Window(FormattedTextControl(text=HTML('<metric>Uptime: <value>2h 15m</value></metric>'))), title="Session"),
        Frame(Window(FormattedTextControl(text=HTML('<metric>Tokens: <value>15,423</value></metric>'))), title="Usage"),
    ])

    middle_section = Frame(
        Window(
            content=FormattedTextControl(text=HTML('<big-content>Main conversation area...</big-content>')),
            wrap_lines=True,
        ),
        title="Conversation"
    )

    bottom_row = VSplit([
        Frame(Window(FormattedTextControl(text=HTML('<mini>System logs...</mini>'))), title="Logs"),
        Frame(Window(FormattedTextControl(text=HTML('<mini>Performance...</mini>'))), title="Stats"),
    ])

    return Layout(HSplit([
        top_row,
        middle_section,
        bottom_row,
    ]))


# Color schemes
THEMES = {
    "dark": {
        'bg': '#1a1a1a',
        'fg': '#ffffff',
        'accent': '#00aaff',
        'success': '#00ff00',
        'warning': '#ffaa00',
        'error': '#ff0000',
    },
    "light": {
        'bg': '#ffffff',
        'fg': '#000000',
        'accent': '#0066cc',
        'success': '#008800',
        'warning': '#cc6600',
        'error': '#cc0000',
    },
    "nord": {
        'bg': '#2e3440',
        'fg': '#d8dee9',
        'accent': '#88c0d0',
        'success': '#a3be8c',
        'warning': '#ebcb8b',
        'error': '#bf616a',
    }
}