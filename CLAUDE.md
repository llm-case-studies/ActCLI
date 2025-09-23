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

**Interactive UI (VSCode-style interface):**
```bash
actcli                        # Default VSCode-style interface
ACTCLI_LAYOUT=vscode actcli   # Explicit VSCode layout
ACTCLI_LAYOUT=claude actcli   # Claude CLI-style layout
ACTCLI_LAYOUT=basic actcli    # Basic terminal layout
```

**Linting and formatting (from AGENTS.md):**
```bash
ruff check src tests
ruff format src tests
```

**Testing:**
```bash
pytest -q                                    # Run all tests quietly
pytest --cov=actcli --maxfail=1 -q          # With coverage, stop on first failure
pytest tests/unit/                          # Unit tests only
pytest tests/integration/                   # Integration tests only
pytest tests/semhost/                       # Semhost API tests
pytest -k "test_specific_function"          # Run specific test pattern
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

# Fresh reset and single action (alternative to serve+action)
scripts/fresh.sh reset                    # Just reset server
scripts/fresh.sh models list            # Reset + list models
```

## Architecture Overview

ActCLI is a terminal-native toolkit for actuarial workflows with multi-model "roundtable" chat capabilities. The codebase follows a layered architecture:

**Core Structure:**
- `src/actcli/cli.py` - Main Typer-based CLI entry point
- `src/actcli/commands/` - Individual command implementations (chat, doctor, auth, models, pr, mcp, wizard, trust, init)
- `src/actcli/ui/` - Terminal user interface implementations
  - `vscode_layout.py` - VSCode-style interface with sidebar and themes
  - `claude_layout.py` - Claude CLI-inspired minimal layout
  - `enhanced_layout.py` - Advanced UI examples and components
- `src/actcli/seminar/` - Multi-model coordination system
  - `coordinator.py` - Orchestrates concurrent model responses
  - `synthesizer.py` - Combines multi-round discussions
  - `adapters/` - Provider-specific adapters (Ollama, OpenAI, Anthropic, Gemini, CodexCLI, Echo)
  - `factory.py` - Adapter factory and model registration
  - `rounds.py` - Multi-round orchestration system
- `src/actcli/auth/` - Authentication and credential management
- `src/actcli/git/` - Git integration utilities
- `src/actcli/mcp/` - Model Context Protocol integration
- `src/semhost/` - FastAPI backend server for web interface
  - `routers/` - API endpoints (sessions, models, pricing, conversations, etc.)
  - `services/` - Business logic (orchestrator, export, pricing, etc.)
  - `schemas/` - Pydantic data models

**Key Patterns:**
- Commands are loaded lazily to minimize import costs
- Multi-model chat uses concurrent execution with timeout handling
- Local model storage under `./models` directory for project isolation
- Rich console output with `--no-color` support throughout
- Environment variable `ACTCLI_MODE` controls hybrid vs offline behavior
- **UI System**: `prompt_toolkit` Application framework for full-screen terminal control
- **Layout Selection**: Environment variable `ACTCLI_LAYOUT` (vscode/claude/basic)
- **Theme Support**: Dynamic color schemes (dark/light/nord) with real-time switching

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
- Test structure: `tests/unit/`, `tests/integration/`, `tests/semhost/` with pytest framework
- Dependencies: uses Typer for CLI, Rich for output, FastAPI for backend, Pydantic for schemas

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.