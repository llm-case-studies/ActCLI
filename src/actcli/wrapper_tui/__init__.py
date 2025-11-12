"""
actcli-shell - Multi-terminal TUI for AI communication.

A VSCode-style integrated terminal interface with:
- Tab-based navigation between wrapped terminals
- Auto-created local facilitator and session
- Slash commands for control (/add, /connect, etc.)
- Progressive complexity (local → docker → remote)
"""

from .shell import Shell

__all__ = ["Shell"]
