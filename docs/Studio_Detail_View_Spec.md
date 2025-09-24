# ActCLI Studio — Model “Detail View” (VSCode Layout)

Purpose
- Add a right-side Detail View (or new Editor Tab) when clicking a model in Models page.
- Provide richer context (pricing, policy, hints, recent usage) and quick actions (1×1 chat; add to seminar; CLI model switch).
- Fit within the existing VSCode-style shell (Activity Bar, Side Bar, Editor Tabs, Bottom Panel, Status Bar).

Trigger
- Click a row in Models → open Detail View.

Layout
- Header: `provider:id` with badges: availability, source, auth, policy.
- Sections:
  - Identity: provider, id, source, auth_mechanism/state, policy_allowed, available, hint.
  - Pricing: from `/pricing`. Show model, unit, input/output, currency; link `source_url` if present. CLI fallback: “subscription (CLI subscription/free tier; see vendor docs)”.
  - Recent Usage: newest-first list (limit N): time, session_id, round, alias, ok/error, latency, text excerpt with “View full”. Link “Open session” (loads in Seminar tab).
  - Actions:
    - 1×1 Chat (inline): textbox prompt; switches `raw` (default true), `disable_tools` (default true); “Run” → `POST /chat/one`; show result below (respect `raw/disable_tools`).
    - Add to Seminar: if in-memory sessions exist → dropdown of `session_id`s; “Add participant” (toast on success). Else → “Create session with this model” (pre-fills participants).
    - CLI model switch (CLI providers only): button “Use fast model” → `POST /providers/cli/model`. Profiles: Codex → `gpt-5-codex`; Gemini → `gemini-1.5-flash-latest`. On success, refresh Models + Detail View.

Models page fixes
- Pricing column: map by `provider:id`; CLI fallback “subscription”.
- Sorting/filtering: by `available`, `provider`; search by `id`.
- Refresh action persists filters.

Seminar IDE (minimum polish)
- Participants: table rows + Presets (Fast Trio, Local Only); “Advanced JSON” toggle (Monaco) roundtrips with table.
- Prompt composer: input + Raw/Clean + Disable tools (applies to `/chat/one` preview only).
- Controls: Create / Start / Next / Export (link to produced markdown).
- Live Grid: latest round entries (alias | ok | latency | text excerpt) with expand to full text.

Ollama State (UI + API)
- UI: “Ollama” panel under Models or sub-tab listing tags (name, size, modified); search.
- Pull model: `POST /ollama/pull name=…`; stream line progress to Panel → Console.
- API (Semhost): `GET /ollama/tags`, `POST /ollama/pull` (SSE/lines; if needed, line chunks / polling).

WS safety & backoff
- Reconnect strategy for `/sessions/{id}/stream`:
  - Exponential backoff: 1s → 2 → 4 → 8 → … cap 30s; stop after 5 minutes or when page is hidden.
  - Show “Offline” banner with “Retry” when disconnected; Connect/Disconnect toggle in Seminar tab.
  - Close WS when tab closes or session changes.

Server endpoints (additions)
- `GET /history?provider=&id=&limit=50`
  - Response (newest first):
  ```jsonc
  [
    {
      "session_id": "abcd1234",
      "session_created_at": 1737684234.12,
      "round_index": 3,
      "alias": "codex",
      "ok": true,
      "latency_ms": 17500,
      "text_excerpt": "The biggest challenge...",
      "started_at": 1737684290.30
    }
  ]
  ```
  - Implementation: read `out/sessions/<id>/round-*.json`; include entries where model_id==id (provider inferred from participants mapping or prefix); skip unreadable files.
- Optional: `GET /sessions`
  - Response: `[{ "id":"abcd1234", "created_at": 1737684234.12, "participants": ["codex","claude","llama"], "round_idx": 2 }]`
  - Use to populate “Add to Seminar” dropdown (or rely on UI-tracked list).

Leverage existing endpoints
- `/chat/one`: `timeout_s` is scheduler cap (top-level). `raw` default true. `disable_tools` default true. `bound_params.timeout_s` is ignored for 1×1.
- `/providers/cli/model` for CLI switches. `/providers/settings` for probe timeout/debug.
- `/pricing` for hints. `/conversations/{id}/export` for report.

SPA implementation pointers
- Networking: small client wrapper around fetch using the Status Bar Server URL; error toasts.
- Detail View: progressive fetch (pricing/history); disable buttons + spinners on actions; toast on result.
- WS backoff: keep a ref; apply delays; stop on hidden; update Status Bar indicator; manual “Retry”.
- Persist: theme, server, last active tab, last session id, panel sizes (localStorage).

Acceptance
- Detail View opens on row click; shows full info + pricing (or subscription) + recent usage; actions work (1×1; add to seminar; CLI switch).
- Pricing column filled for API providers; “subscription” for CLI.
- WS reconnection has backoff and visible status; manual retry works.
- Ollama tag list visible; pull streams progress lines.

Docs to update
- Semhost API Spec: add `/history`, optional `/sessions`, expand `/chat/one` examples and notes; mention `/ui` static serving.
- STATUS: add “Detail View” + WS backoff + Ollama panel to Near‑Term.
- Providers/Auth: note `disable_tools` semantics; call out containerized Semhost with CLI-in-image as clean alternative for demos.

PR plan
- feat(studio): model Detail View (actions + history)
- feat(semhost): add `/history` and optional `/sessions`
- feat(studio): WS backoff + Ollama tags/pull panel
- docs: spec and examples (chat/one, history, `/ui` serving)

