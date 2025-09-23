# API Extensions — Sprint 4 (Design Spec)

Purpose
- Add small, high‑leverage endpoints that improve operations, pricing transparency, and export/archival of seminars.
- Keep endpoints localhost‑only and safe; no secrets in browser.

## Providers & Pricing

Endpoints
- GET /pricing → PricingCatalog
  - Returns coarse pricing info per provider/model: subscription vs per‑token vs per‑request vs free layer.
  - Example row: `{ provider: 'openai', id: 'gpt-4o-mini', pricing: { model: 'per-token', unit: '1K tokens', input: 0.15, output: 0.60, currency: 'USD' } }`
  - CLI‑backed rows typically: `{ model: 'subscription', note: 'billed by vendor CLI subscription' }`.

Notes
- Values are hints for selection (not a billing source of truth); expose `source_url` for each provider.
- Persist minimal cache to `~/.config/actcli/cache/pricing.json` with a 7‑day TTL.

## Providers Diagnostics

Endpoints
- GET /providers/doctor (existing) — keep
- POST /auth/cli/login (existing) — keep
- NEW POST /providers/cli/model
  - Body: `{ provider: 'codex_cli'|'gemini_cli'|'claude_cli', model: string }`
  - Behavior: best‑effort pre‑switch (e.g., `codex /model gpt-4o-mini`, `gemini /model ...` if supported). Returns `{ok, hint}`.
  - Rationale: allows SPA CTA like “Use faster model”.

## Sessions & Conversations Export

Endpoints
- NEW POST /conversations/{session_id}/export
  - Query: `format=md|json|zip`, `compact=none|window|summarize`, `window_k=2`, `include_events=true|false`
  - Returns: `{ path }` to `out/conversations/<id>/` or raw file when `format=json`.
- NEW POST /conversations/{session_id}/compact (server‑side compaction only)
  - Body: `{ strategy: 'window'|'summarize', window_k?: number }`
  - Produces `compact.json` alongside `session.json` and updates `seminar.md`.

Artifacts
- Directory: `out/conversations/<id>/`
  - `session.json` (rolling snapshot)
  - `round-<n>.json` (per round)
  - `events.ndjson` (optional timeline)
  - `seminar.md` (pretty print), `compact.json` (compacted thread)
  - Optional: `report.md` (marketing‑grade summary)

Compaction Strategies
- `window`: retain last K rounds verbatim; older rounds summarized to 1–2 bullet lines per participant.
- `summarize`: LLM‑assisted (local model allowed) to compress early turns with citations to round indices.

CLI
- `actcli export conversation <session_id> --format md --compact summarize --window-k 2 --out out/conversations/<id>`

## WS & E2E

- Add `artifacts_saved` (existing) and optional `export_saved` events after export/compact.
- Minimal Playwright smoke (later): load `/docs`, simple POST `/sessions`, confirm WS events sequence.

## Security & Policy
- Localhost‑only; respects OFFLINE/HYBRID.
- No cloud calls for compaction unless `cloud_share=true` and explicit `allow_cloud_compaction=true`.

## Backlog Items (Post‑Sprint 4)
- Pricing refresh command `actcli providers pricing --refresh`.
- SPA Models grid: show Pricing column + badges (Subscription, Per‑token, Free tier).
- Export presets: `full`, `compact`, `marketing` (include cover + speed/depth/pricing table).
- Add `SEMHOST_CLI_PATHS` setting to extend PATH for CLI detection (e.g., `~/.npm-global/bin`).
- Add `SEMHOST_CLI_DEBUG=1` to include stderr snippets in responses when CLI errors occur.

