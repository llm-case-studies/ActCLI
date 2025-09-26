from __future__ import annotations

import subprocess
import json
import shutil
from typing import Optional
import os


class ClaudeCLIAdapter:
    """Claude adapter using Claude CLI for subscription-based authentication.

    This adapter leverages the Claude CLI tool for authentication and API calls,
    eliminating the need for API key management or custom OAuth flows.

    Prerequisites:
    - Claude CLI installed: npm install -g @anthropic-ai/claude-code
    - User authenticated: run 'claude' and login via browser

    Benefits:
    - Uses subscription billing (no API keys needed)
    - Always up-to-date with Anthropic's auth methods
    - Same login as Claude CLI users already know
    """

    def __init__(self, model: str = "claude-3-5-sonnet-20241022") -> None:
        self.model = model
        self.name = f"{model}(cli)"
        self.is_local = False
        self.model_version = model

        # Check if Claude CLI is available
        if not shutil.which("claude"):
            raise RuntimeError(
                "Claude CLI not found. Install with: npm install -g @anthropic-ai/claude-code"
            )

        # Test authentication by making a simple call
        try:
            env = os.environ.copy()
            if env.get("ACTCLI_DISABLE_CLI_MCP") == "1":
                env["NO_MCP"] = "1"
                env["CLAUDE_CLI_DISABLE_TOOLS"] = "1"
                env["CLAUDE_DISABLE_MCP"] = "1"
                env["MCP_CONFIG"] = ""
                env["MCP_ENDPOINTS"] = ""
            test_result = subprocess.run(
                ["claude", "-p", "test", "--output-format", "json"],
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )

            if test_result.returncode != 0:
                raise RuntimeError(
                    "Claude CLI not authenticated. Run 'claude' and login via browser."
                )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude CLI timeout - authentication may be required")
        except Exception as e:
            raise RuntimeError(f"Claude CLI error: {e}")

    def generate(
        self,
        prompt: str,
        *,
        system: str = "",
        seed: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout_s: int = 30,
        round_index: int = 1,
        context_snippets: Optional[str] = None,
    ) -> str:
        """Generate response using Claude CLI."""

        # Build the full prompt based on round context
        if round_index == 1:
            full_prompt = prompt
        else:
            ctx = context_snippets or ""
            full_prompt = f"Original prompt: {prompt}\nPeers said (snippets):\n{ctx}\nCritique/support briefly and propose one next check."

        # Add system message if provided
        if system:
            full_prompt = f"System: {system}\n\nUser: {full_prompt}"

        # Build Claude CLI command with model selection
        cmd = ["claude", "-p", full_prompt, "--output-format", "json"]

        # Add model parameter if specified
        if self.model and self.model != "default":
            cmd.extend(["--model", self.model])

        # Note: Claude CLI doesn't expose all parameters like temperature/seed
        # These could be added to the prompt if needed for specific use cases

        try:
            env = os.environ.copy()
            if env.get("ACTCLI_DISABLE_CLI_MCP") == "1":
                env["NO_MCP"] = "1"
                env["CLAUDE_CLI_DISABLE_TOOLS"] = "1"
                env["CLAUDE_DISABLE_MCP"] = "1"
                env["MCP_CONFIG"] = ""
                env["MCP_ENDPOINTS"] = ""
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout_s, env=env
            )

            if result.returncode != 0:
                error_msg = (
                    result.stderr.strip()
                    if result.stderr
                    else "Unknown Claude CLI error"
                )
                raise RuntimeError(f"Claude CLI failed: {error_msg}")

            # Parse JSON response
            try:
                data = json.loads(result.stdout.strip())
                response_text = (
                    data.get("result")
                    or data.get("text")
                    or data.get("output")
                    or data.get("content")
                    or result.stdout.strip()
                )
                return str(response_text).strip()
            except json.JSONDecodeError:
                # Fallback to raw output if JSON parsing fails
                return result.stdout.strip()

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"Claude CLI timeout after {timeout_s}s")
        except Exception as e:
            raise RuntimeError(f"Claude CLI error: {e}")
