from __future__ import annotations

from typing import Optional

from rich.console import Console
from rich.panel import Panel

from ..auth.providers import ProviderRegistry


console = Console()


def run_auth(action: str, provider: Optional[str], method: Optional[str], client_id: Optional[str] = None) -> None:
    registry = ProviderRegistry.default()
    action = action.lower()
    if action == "status":
        rows = []
        for pid, prov in registry.providers.items():
            st = prov.status()
            rows.append(f"[cyan]{pid}[/cyan]: {st}")
        console.print(Panel("\n".join(rows) or "No providers", title="Auth Status", border_style="cyan"))
        return

    if provider is None:
        console.print("Specify a provider for this action: openai|anthropic|google")
        raise SystemExit(2)

    prov = registry.get(provider)
    if prov is None:
        console.print(f"Unknown provider: {provider}")
        raise SystemExit(2)

    if action == "login":
        # Vendor CLI-backed providers: trigger their interactive login flows
        if provider in ("codex_cli", "claude_cli"):
            import shutil, subprocess
            cmd = "codex" if provider == "codex_cli" else "claude"
            if not shutil.which(cmd):
                console.print(Panel(
                    f"{cmd} CLI not found.\n\nInstall and sign in:\n- Codex: npm i -g @openai/codex (or brew install codex), then run 'codex'\n- Claude: npm i -g @anthropic-ai/claude-code, then run 'claude'",
                    title=f"{provider} login",
                    border_style="red",
                ))
                raise SystemExit(2)
            console.print(Panel(
                f"Launching {cmd} for interactive login. Follow the on-screen steps, then return to ActCLI.",
                title=f"{provider} login",
                border_style="cyan",
            ))
            try:
                # Hand off to the vendor CLI; user exits when done
                subprocess.run([cmd], check=False)
            except Exception as e:
                console.print(Panel(str(e), title=f"{provider} login error", border_style="red"))
                raise SystemExit(2)
            return

        if provider == "google" and method in ("device", None):
            # Simple Google login like Gemini CLI - use Google's default client ID
            from ..auth.providers import GoogleOAuthDevice
            # Google's public CLI client ID (same as used by gcloud, etc.)
            default_client_id = "764086051850-6qr4p6gpi6hn506pt8ejuq83di341hur.apps.googleusercontent.com"
            cid = client_id or default_client_id

            console.print("\n[bold cyan]How would you like to authenticate for this project?[/bold cyan]")
            console.print("1. [green]Login with Google[/green] (recommended)")
            console.print("2. [yellow]Use Gemini API Key[/yellow] (for IT professionals)")
            console.print("3. [yellow]Vertex AI[/yellow] (for IT professionals)")
            console.print("\n[dim](Use Enter to select)[/dim]")

            choice = input("Choice (1-3): ").strip() or "1"

            if choice == "1":
                from ..auth.google import login_with_google
                login_with_google()
            elif choice == "2":
                console.print("\n[yellow]For IT professionals: Set GOOGLE_API_KEY environment variable[/yellow]")
                console.print("Get your key from: https://makersuite.google.com/app/apikey")
                return
            elif choice == "3":
                console.print("\n[yellow]For IT professionals: Use Google Cloud Vertex AI setup[/yellow]")
                console.print("See: https://cloud.google.com/vertex-ai/docs/generative-ai/start/quickstarts")
                return
            else:
                console.print("Invalid choice. Using Google login...")
                auth = GoogleOAuthDevice(registry.providers["google"].store, cid)  # type: ignore
                auth.login()
                console.print("✅ [green]Logged in to Google successfully![/green]")
                return

        prov.login(preferred_method=method)
        console.print(f"Logged in to {provider} (method: {prov.method or 'unknown'})")
    elif action == "logout":
        prov.logout()
        console.print(f"Logged out of {provider}")
    else:
        console.print("Unknown action. Use: login|status|logout")
        raise SystemExit(2)
