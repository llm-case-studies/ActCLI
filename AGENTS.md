# Repository Guidelines

## Project Structure & Module Organization
- Root: product docs/specs (e.g., `ActCLI_Tier0_Tier1_Spec.md`).
- `Examples/`: reference only; do not modify.
- Source (planned): `src/actcli/`
  - `commands/` (CLI: chat, reserve, plugin, auth, doctor)
  - `seminar/` (adapters, coordinator, synthesizer, policy, transcript)
  - `trust/` (hashing, repro, audit schema)
- Tests: `tests/` with `unit/`, `integration/`, and fixtures under `tests/data/`.

## Build, Test, and Development Commands
- Python 3.11+ required.
- Setup: `python -m venv .venv && source .venv/bin/activate && pip install -e .[dev]`
- Lint/format: `ruff check src tests` • `ruff format src tests`
- Tests: `pytest -q` or with coverage `pytest --cov=actcli --maxfail=1 -q`
- Run locally (when CLI wired): `python -m actcli chat --mode offline`

## Coding Style & Naming Conventions
- Python: 4-space indent, type hints required, smallest public surface.
- Names: modules `lower_snake`, functions/vars `snake_case`, classes `PascalCase`.
- CLI flags/subcommands: lowercase, hyphenated (e.g., `--no-color`).
- Logs/output: minimal by default; use `rich` for legible tables; respect `--no-color`.

## Testing Guidelines
- Framework: `pytest`; target ≥80% coverage for new/changed code.
- File naming: `tests/unit/test_*.py`, `tests/integration/test_*.py`.
- Determinism: seed-sensitive paths must fix seeds; assert stable audit fields when enabled.
- No network in tests unless explicitly marked; stub model adapters.

## Commit & Pull Request Guidelines
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
  - Examples: `feat(chat): add roundtable R2`, `fix(coordinator): timeout handling`.
- PRs include: scope/intent, linked issues, test notes/coverage deltas, and sample CLI output/screenshots.
- Update docs when commands/flags/paths change; keep `Examples/` untouched.

## Security & Configuration Tips
- Default to offline/local models; hybrid/cloud behind explicit user action.
- Secrets via env/OS keychain; never commit keys; prefer `keyring` storage.
- Local config: `actcli.toml` at project root; user trust files under `~/.config/actcli/`.
- Artifacts default to `out/` (e.g., `report.pdf`, `audit.json`, `repro.sh`, `seminar.md`).

