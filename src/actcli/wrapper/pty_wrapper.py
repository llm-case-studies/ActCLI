"""PTY-based terminal wrapper for AI CLI interception."""

import asyncio
import os
import pty
import select
import sys
import termios
import tty
from typing import Callable, List, Optional


class PTYWrapper:
    """
    Wraps an AI CLI using a pseudo-terminal (PTY).

    Intercepts stdin/stdout and allows injection of messages from
    the facilitator service.
    """

    def __init__(
        self,
        command: List[str],
        on_output: Optional[Callable[[str], None]] = None,
        on_input: Optional[Callable[[str], None]] = None,
    ):
        """
        Initialize the PTY wrapper.

        Args:
            command: Command to execute (e.g., ["claude", "chat"])
            on_output: Callback when wrapped process outputs
            on_input: Callback when user inputs
        """
        self.command = command
        self.on_output = on_output
        self.on_input = on_input
        self.master_fd: Optional[int] = None
        self.original_tty_attrs = None
        self._message_queue = asyncio.Queue()

    def inject_message(self, message: str):
        """
        Inject a message into the wrapped process's stdin.

        This allows the facilitator to send messages that appear
        as if the user typed them.
        """
        try:
            self._message_queue.put_nowait(message + "\n")
        except Exception as e:
            print(f"Error injecting message: {e}", file=sys.stderr)

    async def _process_message_queue(self):
        """Process queued messages for injection."""
        while True:
            try:
                message = await asyncio.wait_for(
                    self._message_queue.get(), timeout=0.1
                )
                if self.master_fd:
                    # Write to master fd (appears as stdin to child)
                    os.write(self.master_fd, message.encode())
            except asyncio.TimeoutError:
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"Error processing queue: {e}", file=sys.stderr)
                await asyncio.sleep(0.1)

    def run(self):
        """
        Run the wrapped command in a PTY.

        This is the main loop that:
        1. Creates PTY
        2. Forks and execs the command
        3. Forwards stdin/stdout
        4. Injects facilitator messages
        """
        # Save terminal settings
        if sys.stdin.isatty():
            self.original_tty_attrs = termios.tcgetattr(sys.stdin)

        try:
            # Fork with PTY
            pid, master_fd = pty.fork()

            if pid == 0:
                # Child process - exec the command
                os.execvp(self.command[0], self.command)
            else:
                # Parent process - handle I/O
                self.master_fd = master_fd
                self._run_io_loop(master_fd)

        finally:
            # Restore terminal settings
            if self.original_tty_attrs and sys.stdin.isatty():
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_tty_attrs)

    def _run_io_loop(self, master_fd: int):
        """
        Main I/O loop for forwarding data.

        Monitors:
        - stdin (user input) → forward to child + notify callback
        - master_fd (child output) → forward to stdout + notify callback
        - message queue → inject into child stdin
        """
        # Set stdin to raw mode if it's a TTY
        if sys.stdin.isatty():
            tty.setraw(sys.stdin)

        try:
            while True:
                # Check what's ready to read
                readable, _, _ = select.select(
                    [sys.stdin.fileno(), master_fd], [], [], 0.1
                )

                # Check message queue (non-blocking)
                try:
                    message = self._message_queue.get_nowait()
                    os.write(master_fd, message.encode())
                except:
                    pass

                for fd in readable:
                    try:
                        data = os.read(fd, 4096)
                        if not data:
                            # EOF
                            return

                        if fd == sys.stdin.fileno():
                            # User input → forward to child
                            os.write(master_fd, data)
                            if self.on_input:
                                self.on_input(data.decode('utf-8', errors='ignore'))

                        elif fd == master_fd:
                            # Child output → forward to stdout (needed for terminal display)
                            os.write(sys.stdout.fileno(), data)
                            if self.on_output:
                                self.on_output(data.decode('utf-8', errors='ignore'))

                    except OSError:
                        # Process died
                        return

        except KeyboardInterrupt:
            pass


async def wrap_ai_cli_async(
    command: List[str],
    facilitator_client,
    participant_name: str,
):
    """
    Async wrapper that connects AI CLI to facilitator.

    Args:
        command: AI CLI command (e.g., ["claude", "chat"])
        facilitator_client: Connected FacilitatorClient
        participant_name: Name for this participant
    """
    loop = asyncio.get_event_loop()

    # Buffer to accumulate input until newline
    input_buffer = []

    # Callback for when user types input
    def on_user_input(text: str):
        """Forward user input to facilitator."""
        # Buffer characters until we get a newline
        input_buffer.append(text)

        # Check if we have a complete line
        combined = ''.join(input_buffer)
        if '\n' in combined or '\r' in combined:
            # Extract complete lines
            lines = combined.splitlines(keepends=True)

            # Keep incomplete line in buffer
            if lines and not (lines[-1].endswith('\n') or lines[-1].endswith('\r')):
                incomplete = lines.pop()
                input_buffer.clear()
                input_buffer.append(incomplete)
            else:
                input_buffer.clear()

            # Send complete lines to facilitator
            for line in lines:
                clean_line = line.strip()
                if clean_line:  # Don't send empty lines
                    asyncio.run_coroutine_threadsafe(
                        facilitator_client.send_message(
                            content=clean_line,
                            to="all",
                            msg_type="chat",
                        ),
                        loop
                    )

    # Callback for when AI outputs
    def on_ai_output(text: str):
        """Forward AI output to facilitator."""
        # Send output to facilitator so other participants see responses
        asyncio.run_coroutine_threadsafe(
            facilitator_client.send_message(
                content=text,
                to="all",
                msg_type="chat",
            ),
            loop
        )

    wrapper = PTYWrapper(
        command=command,
        on_input=on_user_input,
        on_output=None,  # DISABLE output forwarding to prevent echo loops with 'cat'
    )

    # Callback for when facilitator sends messages
    async def on_facilitator_message(data: dict):
        """Handle messages from facilitator."""
        if data.get("type") == "chat":
            content = data.get("content", "")
            from_participant = data.get("from", "")

            # Don't echo our own messages back
            if from_participant == facilitator_client.participant_id:
                return

            from_name = data.get("from_name", "Unknown")

            # Format the message nicely
            formatted = f"\n[{from_name}]: {content}\n"
            wrapper.inject_message(formatted)

    # Start listening to facilitator in background
    listen_task = asyncio.create_task(
        facilitator_client.listen(on_facilitator_message)
    )

    # Run the wrapper in executor, but keep event loop alive
    try:
        await loop.run_in_executor(None, wrapper.run)
    except KeyboardInterrupt:
        pass
    finally:
        # Cleanup
        listen_task.cancel()
        try:
            await listen_task
        except asyncio.CancelledError:
            pass
