"""actcli-bench: Experimental TUI with per-tab control plane.

Goals:
- Native-feel terminals (PTY passthrough)
- Independent per-tab binding to facilitator
- Gates: mute in/out, stop-inputs, pause/resume
- Tap windows (temporary unmute)
"""

from __future__ import annotations

import asyncio
import re
import sys
from typing import Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.patch_stdout import patch_stdout

from .session_manager import SessionManager
from .terminal_tab import TerminalManager, TerminalTab
from .binding import TabBinding


class BenchCompleter(Completer):
    def __init__(self) -> None:
        self.commands = {
            "/add": "Add PTY tab (e.g., /add cat)",
            "/switch": "Switch active tab (index or name)",
            "/close": "Close active tab",
            "/bind": "Bind/unbind to facilitator (on|off)",
            "/mute": "Mute in/out/all (on|off)",
            "/stop-inputs": "Stop forwarding user lines to facilitator (on|off)",
            "/pause": "Pause participant (server-side)",
            "/resume": "Resume participant",
            "/tap": "Temporary unmute (in|out) 5s",
            "/sessions": "List sessions",
            "/connect": "Use session context",
            "/viewer": "Show viewer URL",
            "/help": "Show help",
            "/quit": "Exit",
        }

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor.lower()
        if not text.startswith("/"):
            return
        for cmd, desc in self.commands.items():
            if cmd.startswith(text):
                yield Completion(cmd[len(text):], start_position=0, display=f"{cmd} - {desc}")


class BenchShell:
    def __init__(self) -> None:
        self.session_manager = SessionManager()
        self.terminal_manager = TerminalManager()
        self.history = InMemoryHistory()
        self.completer = BenchCompleter()
        self.running = False

        # Bindings: tab.name -> TabBinding
        self.bindings: Dict[str, TabBinding] = {}

        # Tap timers: name -> asyncio.Task
        self._tap_tasks: Dict[str, asyncio.Task] = {}

    # ---------------- UI helpers ----------------
    def _style(self) -> Style:
        return Style.from_dict({
            "navbar": "bg:#2d2d30 #d4d4d4",
            "status": "bg:#1e1e1e #808080",
            "prompt": "#00aaaa bold",
            "bottom-toolbar": "bg:#222222 #cccccc",
        })

    def _navbar(self) -> str:
        parts: List[str] = []
        for i, tab in enumerate(self.terminal_manager.tabs):
            mark = "*" if tab.is_active else ""
            parts.append(f"[{i}:{tab.name}{mark}]")
        if not parts:
            return "No tabs. /add <cmd> to start"
        return " ".join(parts)

    def _status(self) -> str:
        s = self.session_manager.session
        if not s:
            return "No session"
        return f"Session: {s.session_id} | Viewer: {s.facilitator_url}/viewer/{s.session_id}"

    def _bottom_toolbar(self) -> HTML:
        tab = self.terminal_manager.get_active_tab()
        if tab and tab.name in self.bindings:
            b = self.bindings[tab.name]
            bind = "on" if b.subscribed else "off"
            out = "on" if b.send_output_enabled else "off"
            inn = "on" if b.inject_inbound_enabled else "off"
            pin = "on" if b.send_input_enabled else "off"
            paused = "yes" if b.paused else "no"
            alt = "on" if tab.alt_screen else "off"
            info = f"bind:{bind} out:{out} in:{inn} inputs_to_ws:{pin} paused:{paused} alt:{alt}"
        else:
            info = "No binding"
        return HTML(f"<bottom-toolbar>{info} | Ctrl+N/P tabs | /help</bottom-toolbar>")

    def _kb(self) -> KeyBindings:
        kb = KeyBindings()

        @kb.add("c-c")
        def _(event):
            self.running = False
            raise KeyboardInterrupt()

        @kb.add("c-d")
        def _(event):
            self.running = False
            raise EOFError()

        @kb.add("c-n")
        def _(event):
            self.terminal_manager.next_tab()
            print(f"\n➡️  Switched to tab: {self.terminal_manager.get_active_tab().name}\n")

        @kb.add("c-p")
        def _(event):
            self.terminal_manager.prev_tab()
            print(f"\n⬅️  Switched to tab: {self.terminal_manager.get_active_tab().name}\n")

        return kb

    # ---------------- Commands ----------------
    async def _cmd_add(self, args: List[str]):
        if not args:
            print("Usage: /add <command> [args...]")
            return
        name = args[0]
        cmd = args
        loop = asyncio.get_event_loop()

        def on_output_factory(tab_name: str):
            def _on_output(data: bytes):
                text = data.decode("utf-8", errors="replace")
                b = self.bindings.get(tab_name)
                if b:
                    b.handle_process_output(text, loop)
            return _on_output

        tab = self.terminal_manager.add_tab(name, cmd, on_output=on_output_factory(name))
        # Create detached binding (not connected yet)
        if self.session_manager.session:
            s = self.session_manager.session
            self.bindings[name] = TabBinding(
                name=name,
                facilitator_url=s.facilitator_url,
                session_id=s.session_id,
            )
        print(f"Added tab [{name}]. Use /bind on to connect.")

    async def _cmd_switch(self, token: str):
        if token.isdigit():
            self.terminal_manager.switch_tab(int(token))
            return
        for i, t in enumerate(self.terminal_manager.tabs):
            if t.name == token:
                self.terminal_manager.switch_tab(i)
                return
        print("Tab not found")

    async def _cmd_close(self, token: Optional[str]):
        idx = None
        if token and token.isdigit():
            idx = int(token)
        elif token:
            for i, t in enumerate(self.terminal_manager.tabs):
                if t.name == token:
                    idx = i
                    break
        else:
            idx = self.terminal_manager.active_index
        if idx is None:
            print("No such tab")
            return
        tab = self.terminal_manager.tabs[idx]
        # Unbind if bound
        b = self.bindings.pop(tab.name, None)
        if b and b.subscribed:
            await b.unbind()
        self.terminal_manager.close_tab(idx)
        print("Closed tab")

    async def _cmd_bind(self, arg: str):
        tab = self.terminal_manager.get_active_tab()
        if not tab:
            print("No active tab")
            return
        b = self.bindings.get(tab.name)
        if not b:
            print("No session context. /connect or start facilitator first.")
            return
        if arg == "on":
            ok = await b.bind()
            if ok:
                await b.start_listening(lambda line: (not tab.alt_screen) and tab.inject_line(f"[{b.name}] {line}"))
                print("Bound to facilitator.")
            else:
                print("Bind failed")
        elif arg == "off":
            await b.unbind()
            print("Unbound")
        else:
            print("Usage: /bind on|off")

    async def _cmd_mute(self, which: str, state: str):
        tab = self.terminal_manager.get_active_tab()
        if not tab:
            print("No active tab")
            return
        b = self.bindings.get(tab.name)
        if not b:
            print("No binding for this tab")
            return
        val = state == "on"
        if which == "out":
            b.send_output_enabled = not val if state in ("on", "off") else b.send_output_enabled
        elif which == "in":
            b.inject_inbound_enabled = not val if state in ("on", "off") else b.inject_inbound_enabled
        elif which == "all":
            b.send_output_enabled = not val
            b.inject_inbound_enabled = not val
        else:
            print("Usage: /mute [in|out|all] on|off (on=mute, off=unmute)")
            return
        print(f"Mute updated: out={b.send_output_enabled} in={b.inject_inbound_enabled}")

    async def _cmd_stop_inputs(self, state: str):
        tab = self.terminal_manager.get_active_tab()
        if not tab:
            print("No active tab")
            return
        b = self.bindings.get(tab.name)
        if not b:
            print("No binding for this tab")
            return
        if state not in ("on", "off"):
            print("Usage: /stop-inputs on|off")
            return
        # on = stop forwarding; off = allow forwarding
        b.send_input_enabled = (state == "off")
        print(f"Forward user-input to WS: {'on' if b.send_input_enabled else 'off'}")

    async def _cmd_pause(self):
        tab = self.terminal_manager.get_active_tab()
        if not tab:
            return
        b = self.bindings.get(tab.name)
        if b and b.subscribed:
            await b.set_paused(True)
            print("Paused (server-side)")

    async def _cmd_resume(self):
        tab = self.terminal_manager.get_active_tab()
        if not tab:
            return
        b = self.bindings.get(tab.name)
        if b and b.subscribed:
            await b.set_paused(False)
            print("Resumed (server-side)")

    async def _cmd_tap(self, which: str, duration: str):
        tab = self.terminal_manager.get_active_tab()
        if not tab:
            return
        b = self.bindings.get(tab.name)
        if not b:
            return
        m = re.match(r"^(\d+)(s)?$", duration)
        if not m:
            print("Usage: /tap (in|out) 5s")
            return
        seconds = int(m.group(1))

        async def _auto_off(flag: str):
            await asyncio.sleep(seconds)
            if flag == "out":
                b.send_output_enabled = False
            else:
                b.inject_inbound_enabled = False
            print(f"tap {flag}: auto-off")

        if which == "out":
            b.send_output_enabled = True
            task = asyncio.create_task(_auto_off("out"))
            self._tap_tasks[tab.name] = task
        elif which == "in":
            b.inject_inbound_enabled = True
            task = asyncio.create_task(_auto_off("in"))
            self._tap_tasks[tab.name] = task
        else:
            print("Usage: /tap (in|out) 5s")

    async def _cmd_sessions(self):
        sessions = await self.session_manager.list_sessions()
        if not sessions:
            print("No sessions")
            return
        for s in sessions:
            print(f"  {s['id']} - {s['name']} ({s['participant_count']} participants)")

    async def _cmd_connect(self, session_id: str):
        ok = await self.session_manager.use_session(session_id)
        print("Connected to session" if ok else "Failed to connect")

    async def _cmd_viewer(self):
        s = self.session_manager.session
        if not s:
            print("No session")
            return
        print(f"Viewer: {s.facilitator_url}/viewer/{s.session_id}")

    async def _cmd_help(self):
        print(
            """
Commands:
  /add <cmd>            Add new PTY tab (e.g., /add cat)
  /switch <idx|name>    Switch to tab
  /close [idx|name]     Close a tab

  /bind on|off          Bind/unbind active tab to facilitator
  /mute in|out|all on|off   Mute streams (on=mute, off=unmute)
  /stop-inputs on|off   Stop forwarding user-entered lines to facilitator
  /pause | /resume      Server-side participant pause/resume
  /tap in|out 5s        Temporary unmute for N seconds

  /sessions             List sessions
  /connect <id>         Use session (future binds use this)
  /viewer               Show broadcast viewer URL
  /help                 Show this help
  /quit                 Exit
            """
        )

    # ---------------- Main loop ----------------
    async def _initialize(self):
        print("\n=== actcli-bench ===")
        print("Starting local facilitator...")
        if await self.session_manager.start_local_facilitator():
            print("✅ Facilitator ready")
            if await self.session_manager.create_default_session():
                s = self.session_manager.session
                print(f"✅ Session: {s.session_id}")
                print(f"Viewer: {s.facilitator_url}/viewer/{s.session_id}")
        else:
            print("❌ Facilitator not available")

    async def run_async(self):
        await self._initialize()

        session = PromptSession(
            history=self.history,
            completer=self.completer,
            key_bindings=self._kb(),
            style=self._style(),
            bottom_toolbar=self._bottom_toolbar,
            complete_while_typing=False,
            mouse_support=False,
        )
        self.running = True

        with patch_stdout():
            while self.running:
                try:
                    # Status area
                    print("\n" + self._navbar())
                    print(self._status())

                    text = await session.prompt_async(HTML("\n<prompt>actcli-bench></prompt> "))
                    if text is None:
                        break
                    text = text.strip()
                    if not text:
                        continue

                    # Slash commands
                    if text.startswith("/"):
                        parts = text[1:].split()
                        cmd = parts[0].lower()
                        args = parts[1:]
                        if cmd == "add":
                            await self._cmd_add(args)
                        elif cmd == "switch" and args:
                            await self._cmd_switch(args[0])
                        elif cmd == "close":
                            await self._cmd_close(args[0] if args else None)
                        elif cmd == "bind":
                            await self._cmd_bind(args[0] if args else "on")
                        elif cmd == "mute" and len(args) == 2:
                            await self._cmd_mute(args[0], args[1])
                        elif cmd == "stop-inputs" and args:
                            await self._cmd_stop_inputs(args[0])
                        elif cmd == "pause":
                            await self._cmd_pause()
                        elif cmd == "resume":
                            await self._cmd_resume()
                        elif cmd == "tap" and len(args) == 2:
                            await self._cmd_tap(args[0], args[1])
                        elif cmd == "sessions":
                            await self._cmd_sessions()
                        elif cmd == "connect" and args:
                            await self._cmd_connect(args[0])
                        elif cmd == "viewer":
                            await self._cmd_viewer()
                        elif cmd == "help":
                            await self._cmd_help()
                        elif cmd == "quit":
                            break
                        else:
                            print("Unknown command; /help")
                    else:
                        # Regular input goes to active tab and maybe forwarded to facilitator
                        tab = self.terminal_manager.get_active_tab()
                        if not tab:
                            print("No active tab. /add <cmd> to start")
                            continue
                        # Always send to process for native feel
                        tab.write_input((text + "\n").encode())
                        # Optionally forward to facilitator
                        b = self.bindings.get(tab.name)
                        if b:
                            await b.send_user_line(text)

                    await asyncio.sleep(0.05)
                except (EOFError, KeyboardInterrupt):
                    break
                except Exception as e:
                    print(f"Error: {e}")

        await self._cleanup_async()

    async def _cleanup_async(self):
        # Unbind all
        for b in list(self.bindings.values()):
            try:
                await b.unbind()
            except Exception:
                pass
        self.terminal_manager.close_all()
        self.session_manager.cleanup()

    def run(self):
        try:
            asyncio.run(self.run_async())
        except KeyboardInterrupt:
            pass


def main():
    # TTY safeguard similar to actcli-shell
    if not sys.stdin.isatty():
        print("Error: actcli-bench requires a TTY", file=sys.stderr)
        sys.exit(1)
    BenchShell().run()


if __name__ == "__main__":
    main()

