# ActCLI (prototype)

ActCLI is a terminal‑native toolkit for actuarial workflows with a multi‑model "roundtable" chat. This scaffold demonstrates the WOW path: concurrent responses from multiple models, a second round that references peers, and a simple synthesis. It also includes a first‑run doctor and stubbed auth.

## Quickstart

- Python 3.11+
- Create venv and install:
  - `python -m venv .venv && source .venv/bin/activate`
  - `pip install -e .`
- Health check:
  - `actcli doctor`
- Roundtable demo:
  - `actcli chat --prompt "Compare reserving strategies" --multi llama3,claude,gpt --rounds 2`
- Auth status (API keys via env):
  - `actcli auth status`

## Layout (scaffold)
- `src/actcli/cli.py` — Typer entry (`actcli`)
- `src/actcli/commands/` — `chat`, `doctor`, `auth`
- `src/actcli/seminar/` — adapters, coordinator, synthesizer
- `src/actcli/auth/` — provider registry and credential store

Notes
- Adapters currently use an `EchoAdapter` (no network) to validate concurrency and UX. Real providers (OpenAI/Anthropic/Google, Ollama) can be plugged in next.
- `doctor` prints a concise readiness summary to build user confidence on first run.
- Auth supports API key envs now; OAuth device/PKCE will be added via provider plugins.

## Local models in this repo

Run a project-scoped Ollama server that stores models under `./models`:

- Start server: `scripts/ollama-local.sh serve` (port 11435; models in `./models`)
- Pull defaults: `scripts/ollama-local.sh pull-all` (codellama:34b, gpt-oss:20b, codellama:13b, llama3:8b, llama3.2:3b)
- List via CLI: `actcli models list --ollama-host http://127.0.0.1:11435`
- Use in chat: `actcli chat --multi "codellama:34b,gpt-oss:20b,codellama:13b" --rounds 2 --ollama-host http://127.0.0.1:11435`

### One-shot runner (fresh start + action)

- Fresh reset and pull all defaults:
  - `scripts/fresh.sh pull-all`
- Fresh reset and run a chat:
  - `scripts/fresh.sh chat --prompt "Compare approaches" --multi "codellama:34b,gpt-oss:20b,codellama:13b"`
- Fresh reset and list models:
  - `scripts/fresh.sh models list`

