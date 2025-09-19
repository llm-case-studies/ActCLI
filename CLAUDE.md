# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Setup:**
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
```

**Health check:**
```bash
actcli doctor
```

**Linting and formatting (from AGENTS.md):**
```bash
ruff check src tests
ruff format src tests
```

**Testing (when tests exist):**
```bash
pytest -q
pytest --cov=actcli --maxfail=1 -q  # with coverage
```

**Local Ollama server management:**
```bash
# Start project-local Ollama server (port 11435, models in ./models)
scripts/ollama-local.sh serve

# Pull default models
scripts/ollama-local.sh pull-all

# Fresh reset + action (kills existing server, starts new one)
scripts/fresh.sh pull-all
scripts/fresh.sh chat --prompt "test" --multi "codellama:34b,gpt-oss:20b"
```

## Architecture Overview

ActCLI is a terminal-native toolkit for actuarial workflows with multi-model "roundtable" chat capabilities. The codebase follows a layered architecture:

**Core Structure:**
- `src/actcli/cli.py` - Main Typer-based CLI entry point
- `src/actcli/commands/` - Individual command implementations (chat, doctor, auth, models, pr)
- `src/actcli/seminar/` - Multi-model coordination system
  - `coordinator.py` - Orchestrates concurrent model responses
  - `synthesizer.py` - Combines multi-round discussions
  - `adapters/` - Provider-specific adapters (Ollama, Echo for testing)
- `src/actcli/auth/` - Authentication and credential management
- `src/actcli/git/` - Git integration utilities

**Key Patterns:**
- Commands are loaded lazily to minimize import costs
- Multi-model chat uses concurrent execution with timeout handling
- Local model storage under `./models` directory for project isolation
- Rich console output with `--no-color` support throughout
- Environment variable `ACTCLI_MODE` controls hybrid vs offline behavior

**Multi-Model Chat Flow:**
1. Parse comma-separated provider list (e.g., "llama3,claude,gpt")
2. Coordinator runs providers concurrently with timeouts
3. Second round allows models to reference peer responses
4. Synthesizer combines results into final output

**Authentication:**
- API keys via environment variables
- Future OAuth device/PKCE support planned
- Keyring storage for secure credential management

## File Naming Conventions

- Python modules: `lower_snake_case`
- Classes: `PascalCase`
- Functions/variables: `snake_case`
- CLI flags: lowercase with hyphens (e.g., `--no-color`, `--ollama-host`)
- Test files: `tests/unit/test_*.py`, `tests/integration/test_*.py`

## Important Notes

- Currently uses `EchoAdapter` for testing concurrency/UX without network calls
- Real providers (OpenAI/Anthropic/Google) can be plugged in via adapter pattern
- Default Ollama models: codellama:34b, gpt-oss:20b, codellama:13b, llama3:8b, llama3.2:3b
- Output artifacts default to `out/` directory
- Security: secrets via env/keyring only, never commit API keys
- Python 3.11+ required, 4-space indentation, type hints mandatory