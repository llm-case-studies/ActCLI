# Semhost (FastAPI) — API, Docs, and Test Plan

Progress Tracker (copy/paste into issue)
- [x] Semhost skeleton running on 127.0.0.1:7530
- [x] OpenAPI docs exposed at /openapi.json, /docs, /redoc
- [x] Status: GET/PATCH /status (mode, cloud_share, window_k, max_rounds, read/write)
- [x] Models: GET /models (aggregated local/api/cli with Source/Auth badges)
- [x] Providers doctor: GET /providers/doctor, POST /auth/cli/login
- [ ] SPA shell (VSCode layout): Sidebar + Models + Status pages
- [x] Sessions: POST/GET/PATCH /sessions
- [x] Rounds: POST /sessions/{id}/round/start + /round/next
- [x] Streaming: WS /sessions/{id}/stream (round lifecycle events)
- [x] Persistence parity: out/sessions/<id>/session.json + round-<n>.json
- [x] MCP: GET/PATCH /mcp
- [ ] SPA toggles
- [x] Locations API (GET/PATCH)
- [ ] Locations editor (SPA)
- [ ] Formats catalog: GET /formats + SPA cards (round_robin, delphi_lite, cec)
- [ ] Synthesis panel (summary + disagreement)
- [ ] CLI integration prefers semhost, falls back to in-proc
- [ ] E2E: Playwright flows (Models render; start/next; toggles reflect)

Purpose
- Provide a single local backend for CLI and SPA to share state, orchestrate seminars, and surface availability/status of models and MCP.
- Expose OpenAPI docs for manual verification and scripted/e2e testing.

Principles
- Localhost-first, offline-by-default; explicit user action required to allow cloud sharing.
- Single source of truth: semhost owns session state; CLI may fallback to in-proc with identical behavior.
- No secrets in browser; tokens/keys stay server-side (keyring preferred, file fallback 0600).
- Deterministic artifacts: out/sessions/<id>/session.json and round-<n>.json.

## API Surface (v1)

Folder Structure (scaffold)
```
src/semhost/
  main.py                # app factory + routers (stub)
  settings.py            # pydantic Settings (stub)
  deps.py                # shared dependencies (stub)
  events.py              # WS events (stub)
  routers/
    health.py            # GET /health (stub)
    status.py            # GET/PATCH /status (stub)
    models.py            # GET /models (stub)
    providers.py         # GET /providers/doctor, POST /auth/cli/login (stub)
    formats.py           # GET /formats (stub)
    mcp.py               # GET/PATCH /mcp (stub)
    sessions.py          # session + round endpoints (stub)
    ws.py                # WS /sessions/{id}/stream (stub)
    ollama.py            # optional passthroughs (stub)
  schemas/
    status.py, models.py, providers.py, participants.py, sessions.py, formats.py (stubs)
  services/
    model_aggregator.py, providers_service.py, orchestrator_service.py,
    persistence.py, mcp_service.py, policy_service.py (stubs)

studio/
  README.md              # SPA scaffold and structure

tests/semhost/
  unit/test_routes_scaffold.py
  integration/test_sessions_rounds_scaffold.py
  e2e/README.md
```

OpenAPI & Docs
- OpenAPI JSON: `GET /openapi.json`
- Swagger UI: `GET /docs`
- ReDoc: `GET /redoc`

Status
- `GET /health` → `{ ok: true, version: string }`
- `GET /status` → `{ mode: 'OFFLINE'|'HYBRID', cloud_share: bool, window_k: int, max_rounds: int|null, read: string[], write: string[] }`
- `PATCH /status` body (any subset): `{ mode?, cloud_share?, window_k?, max_rounds?, read?, write? }`

Models
- `GET /models` → `ModelItem[]`
  - ModelItem (compat): `{ provider, id, source, auth, available, description?, blocked_reason? }`
  - Enriched: `{ auth_mechanism, auth_state: 'ready'|'missing'|'signed_out'|'unauthorized'|'unknown', policy_allowed: bool, policy_reason?: 'offline'|'cloud_share_disabled', hint? }`
  - Aggregates: ollama, openai, anthropic, google, claude_cli, codex_cli (later: openai_compat, azure_openai)

Providers (CLI)
- `GET /providers/doctor` → `[ { provider, binary, version, auth, hint } ]`
- `POST /auth/cli/login` body: `{ provider: 'codex_cli'|'claude_cli' }` → `{ launched: true }` (best-effort handoff)

MCP
- `GET /mcp` → `MCPServer[]` where MCPServer: `{ name, url, enabled, group?, desc? }`
- `PATCH /mcp/{name}` body: `{ enabled: bool }` → updated server

Seminar Formats
- `GET /formats` → `SeminarFormat[]` where
  - `{ id: 'round_robin'|'delphi_lite'|'cec', label, description, defaults: { window_k, max_rounds, temperature? } }`

Sessions & Rounds
- `POST /sessions` body: `{ format_id?, participants?, window_k?, max_rounds?, cloud_share? }` → `{ session_id }`
- `GET /sessions/{id}` → full Session snapshot
- `PATCH /sessions/{id}` → update participants/bounds/format
- `POST /sessions/{id}/round/start` body: `{ prompt: string, focus?: string[] }` → `RoundRecord`
- `POST /sessions/{id}/round/next` → `RoundRecord`
- WS `GET /sessions/{id}/stream`
  - Events: `session_start, round_start, turn_result, round_end, artifacts_saved, error`

Ollama (optional)
- `GET /ollama/tags` → passthrough to configured host
- `POST /ollama/pull` body: `{ name: string }` → streaming progress (SSE)

## Data Shapes (concise)
- Participant: `{ alias, spec, bound_params?: { temperature?, system?, seed?, timeout_s? } }`
- RoundRecord: `{ index, started_at, completed_at?, entries: Entry[], synopsis? }`
- Entry: `{ alias, model_id, ok, latency_ms, text?, error?, params_snapshot? }`
- Session: `{ id, created_at, round_idx, max_rounds?, window_k, mode, participants: Participant[], history: RoundRecord[] }`

## CLI & SPA Integration
- CLI preferred: HTTP to semhost (configurable via `--server http://127.0.0.1:7530`), fallback to in-proc when offline.
- SPA (VSCode layout): left sidebar (Models, Seminar, MCP, Locations, Status); main area (Live grid, Prompt, Event log).
- Both surfaces share semhost as backend; artifacts/policy are consistent.

## Security & Privacy
- Bind default `127.0.0.1:7530`; CORS restricted to SPA origin.
- No secrets in browser; OAuth/key management stays server-side.
- OFFLINE blocks cloud participants; HYBRID requires `cloud_share: true`.

## API Docs Usage (manual / scripted)
- Hit `GET /docs` to manually exercise endpoints during dev.
- Script with httpie/curl:
  - `http :7530/models`
  - `http PATCH :7530/status cloud_share:=true`
  - `http POST :7530/sessions prompt='Q' participants:='[ ... ]'`
- WebSocket: use `websocat ws://127.0.0.1:7530/sessions/<id>/stream` (dev only).

## Test Plan

Unit (backend)
- models aggregation returns correct rows given env & CLI mocks
- status GET/PATCH roundtrips and validates ranges
- providers/doctor parses subprocess outputs, timeouts
- sessions POST creates id; PATCH updates participants and bounds; rejects invalid formats

Integration (backend)
- round/start and round/next orchestrate Echo + mocked adapters; persistence files exist
- OFFLINE mode filters cloud; HYBRID with `cloud_share=false` returns cloud-blocked or filtered entries
- WebSocket event sequence: session_start → round_start → N×turn_result → round_end → artifacts_saved

CLI integration
- CLI commands call semhost (when available) for models/status; fallback works when semhost is down
- chat uses semhost endpoints and writes transcript; /share cloud on reflected by semhost PATCH /status

SPA e2e (Playwright)
- Models page renders aggregated table (local/api/cli) with correct Source/Auth badges
- Seminar page: add participants; select format; enter prompt; run a round; see entries populate
- Status pane: toggle MODE/HYBRID and cloud_share; Models table updates availability
- MCP pane: toggle server; state persists
- Locations pane: edit read/write globs; PATCH reflected by GET

Contract tests
- CLI doctor probes: simulate codex/claude subprocess; assert `ok/no/missing`
- Aggregated listing parity with CLI `actcli models list --provider all`

Coverage & Determinism
- Aim ≥80% for new semhost modules; seed-sensitive paths fix seeds
- No network in tests unless marked; use respx/subprocess monkeypatch

## Checklists (Sprints)

Sprint 1 — Shell & Models
- [x] FastAPI app scaffold; bind 127.0.0.1:7530
- [x] `/openapi.json`, `/docs`, `/redoc` exposed (custom title)
- [x] `GET /health`, `GET/PATCH /status` (MODE, cloud_share, window_k, max_rounds, read/write)
- [x] `GET /models` aggregated (local/api/cli), using existing registry logic
- [x] `GET /providers/doctor` (codex/claude probes)
- [ ] SPA shell (VSCode layout): Sidebar + Models + Status pages
- [x] Tests: unit for routes, CLI probe parsing; SPA smoke

Sprint 2 — Sessions & Rounds
- [x] `POST /sessions`, `GET/PATCH /sessions/{id}`; validation
- [x] `POST /sessions/{id}/round/start`; `.../round/next`
- [x] WS `/sessions/{id}/stream` eventing
- [x] Persistence to `out/sessions/<id>`; parity with CLI artifacts
- [ ] SPA: Participants editor (bounds), Format selector (cards), Prompt area, Live grid
- [x] Tests: orchestrator integration; WS sequence
- [ ] Tests: SPA e2e (start/next)

Sprint 3 — MCP & Locations
- [x] `GET/PATCH /mcp`
- [ ] UI toggles
- [x] Locations API (GET/PATCH)
- [ ] Locations editor (SPA)
- [x] Tests: API CRUD
- [ ] Tests: SPA interactions

Sprint 4 — Presets & Polish
- [ ] `/formats` catalog; apply presets (delphi_lite, cec)
- [ ] Synthesis panel and disagreement score (existing synthesizer)
- [ ] Metrics in Status pane; minor UX polish
- [ ] Tests: presets application; synthesis render

Backlog (near-term)
- [ ] “Connect Gemini” OAuth in semhost (Generative Language scope), tokens server-side
- [ ] Keyring-backed secrets; `actcli auth import .env.local`; masked `auth status`
- [ ] `openai_compat` profiles (DeepSeek/Grok); Azure OpenAI profiles
- [ ] Streaming tokens & cost meters; disagreement heatmap; export/import seminar config

Acceptance (Phase 1–2)
- Models & Status pages mirror CLI aggregated view and toggles accurately
- Users can assemble participants, select a format, and run synchronized rounds with live UI updates
- OFFLINE/HYBRID + cloud_share enforced uniformly across CLI/SPA/semhost
- OpenAPI docs enable manual and scripted tests; WS streams reflect round lifecycle
