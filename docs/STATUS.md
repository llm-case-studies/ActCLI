# Implementation Status

This snapshot summarizes what is working now and what’s next.

## What’s Implemented
- No‑flags startup wizard (trust, mode, models, output dir, cloud share) + banner and health panel.
- Roundtable REPL: concurrent fan‑out, 2‑round critique, synthesis; slash commands (/models, /rounds, /ollama, /save, /trust, /allow, /deny, /share).
- Local models: Ollama adapter, project‑local server (./models), streaming pull progress, fresh runner.
- Cloud adapters (API‑key path): OpenAI/Anthropic/Gemini with graceful Echo fallback.
- Config + trust + policy: actcli.toml defaults; trust store; policy guard that filters cloud unless enabled.
- MCP manager: list/add/on/off/test/log/reload/restart; per‑server logs; project/global configs.
- Presenter: lightweight SPA (actcli presenter start) that auto‑reads state.json.

### Semhost (FastAPI backend)
- Sessions API: POST/GET/PATCH /sessions
- Rounds API: /sessions/{id}/round/start and /round/next
- WebSocket streaming: /sessions/{id}/stream with round lifecycle events
- Models API: aggregated local/api/cli with auth/policy fields
- Providers doctor and CLI login handoff
- Deterministic artifacts under out/sessions/<id>

## Near‑Term Roadmap
- MCP stdio deep‑test (spawn + handshake) for non‑HTTP servers (e.g., Serena).
- REPL /mcp ui (TUI) and arrow‑key first‑run wizard.
- Persist /allow and /deny to actcli.toml.
- Optional events.ndjson for Presenter timeline.
 - Semhost Sprint 3: MCP + Locations

## Usage Highlights
- Start: `actcli` → wizard → REPL. Help: `/help`.
- Local models: `scripts/fresh.sh pull-all` then `/ollama http://127.0.0.1:11435`.
- Save outputs: `--save out/seminar.md --audit out/audit.json` or `/save out/seminar.md audit out/audit.json`.
- Presenter: `actcli presenter start` then set `ACTCLI_PRESENTER_STATE=out/presenter/state.json` while chatting.
- MCP: `actcli mcp list|test|log|reload|restart`.
- See Architecture for information flows and controls: ./ARCHITECTURE.md
