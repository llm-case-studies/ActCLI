"""Wrapped terminal that connects to facilitator."""

import asyncio
import os
import pty
import select
from typing import List, Optional

from ..wrapper.client import FacilitatorClient
from ..wrapper.pty_wrapper import wrap_ai_cli_async


class WrappedTerminal:
    """A terminal that's wrapped and connected to facilitator."""

    def __init__(
        self,
        name: str,
        command: List[str],
        session_id: str,
        facilitator_url: str = "http://localhost:8765",
    ):
        self.name = name
        self.command = command
        self.session_id = session_id
        self.facilitator_url = facilitator_url
        self.client: Optional[FacilitatorClient] = None
        self.task: Optional[asyncio.Task] = None
        self.participant_id: Optional[str] = None

    async def start(self):
        """Start the wrapped terminal and connect to facilitator."""
        try:
            # Create client
            self.client = FacilitatorClient(self.facilitator_url)

            # Join session
            self.participant_id = await self.client.join_session(
                session_id=self.session_id,
                name=self.name,
                provider="cli",  # Generic CLI provider
                model=self.name,  # Use name as model identifier
            )

            # Connect WebSocket
            await self.client.connect_websocket()

            # Start the wrapped AI CLI
            self.task = asyncio.create_task(
                wrap_ai_cli_async(self.command, self.client, self.name)
            )

            return True

        except Exception as e:
            print(f"❌ Failed to start {self.name}: {e}")
            return False

    async def stop(self):
        """Stop the wrapped terminal."""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        if self.client:
            await self.client.close()

    def is_running(self) -> bool:
        """Check if terminal is still running."""
        return self.task is not None and not self.task.done()
