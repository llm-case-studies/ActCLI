# Semhost TODOs (Working Checklist)

This is a lightweight task list derived from the Semhost API spec to drive implementation and testing.

Core
- [x] App scaffold (FastAPI), bind 127.0.0.1:7530, CORS for SPA
- [x] /openapi.json, /docs, /redoc with custom title
- [x] /health
- [x] /status GET/PATCH (mode, cloud_share, window_k, max_rounds, read/write)

Models & Providers
- [x] /models aggregated (ollama, openai, anthropic, google, claude_cli, codex_cli)
- [x] /providers/doctor (codex/claude probes); /auth/cli/login handoff

Sessions & Rounds
- [x] /sessions POST (create), GET/PATCH (update), validation
- [x] /sessions/{id}/round/start (prompt, focus); /round/next
- [x] WS /sessions/{id}/stream (session_start, round_start, turn_result, round_end, artifacts_saved)
- [x] Persistence parity to out/sessions/<id>

MCP & Locations
- [ ] /mcp GET/PATCH (list/toggle)
- [ ] Locations read/write PATCH/GET

Formats & UX
- [ ] /formats (round_robin, delphi_lite, cec); defaults applied server-side
- [ ] Synthesis panel hook (summary + disagreement)

CLI & SPA
- [ ] CLI prefers semhost via --server; fallback to in-proc
- [ ] SPA VSCode layout: Sidebar (Models, Seminar, MCP, Locations, Status) + main (Live grid, Prompt, Event log)

Testing
- [x] Unit tests for routes (httpx)
- [x] Integration tests for orchestrator + persistence
- [x] WS event sequence test
- [ ] Playwright e2e (Models render; add participants; start/next; toggles)
- [ ] Contract tests: aggregated list parity with CLI; doctor probes

Backlog (next)
- [ ] “Connect Gemini” OAuth (delegated tokens, server-side storage)
- [ ] Keyring-backed secrets; `actcli auth import .env.local`; masked `auth status`
- [ ] openai_compat profiles (DeepSeek, Grok); Azure OpenAI profiles
- [ ] Streaming tokens & cost meters; disagreement heatmap; export/import seminar config
