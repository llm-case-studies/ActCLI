# Session Resume • Browser Extension (Duplex + Progressive E2E)

This note captures exactly where we paused and how to resume quickly next session.

## Context Snapshot (End of Day)

- Playground mocks shipped: WA/TG/RC/Preply/Slack + Relay (Seminar ↔ Remote) + Shell nav
- Progressive E2E green locally (10/10) including relay.spec
- Feature reference published: `docs/Owners/Browser_Extension/FEATURE_REFERENCE.md`
- Orchestration scripts available: `scripts/playground.sh`, `scripts/pw_playground.sh`, `scripts/pw_orchestrate.sh`, `scripts/seed_rocketchat.sh`
- Next high‑value feature: Popup “Send Text” + Mapping Status (duplex foundation)

## Immediate Next (P1) — Popup “Send Text” + Mapping Status

Goal: From the popup, send arbitrary text through the mapped page so it visibly appears in history AND log MCP events (`participants.message` + `events.log`). Show mapping status at a glance.

Files to touch
- `extensions/generic-chat-bridge/src/ui/popup.html`
- `extensions/generic-chat-bridge/src/ui/popup.js`
- `extensions/generic-chat-bridge/src/background/index.js`
- `extensions/generic-chat-bridge/src/content/index.js`

Message handlers (new/extended)
- Content (page context)
  - `content.getProfile` → returns `{ input, send, history }` from stored profile
  - `content.sendText` → `{ text }` → focus input, insert text, trigger mapped send (button or key combo), observe history; returns `{ ok: true, observed: string|null }` or `{ ok:false, error }`
- Background (service worker)
  - `bridge.sendText` → get active origin; ensure health OK; call `content.sendText`; then MCP:
    - `participants.message` with `{ participant_id?, text, origin }` (use stored participant_id from connect if available)
    - `events.log` with `{ event:'send_text', origin, participant_id?, observed }`
  - Return `{ ok, observed }` (bubble errors in `{ error }`)
- Popup (UI)
  - Add Mapping Status box (Input selector; Send = button selector OR key combo; History selector)
  - Add Send Text row (`#sendText` + `#sendNow`) disabled when health is false
  - On open: fetch config + health + mapping status; update buttons accordingly

Key behaviors
- Keyboard‑based send mapping: if profile.send starts with `__KEY:` (e.g., `__KEY:Enter__`, `__KEY:Ctrl+Enter__`), content should synthesize matching keydown/keyup on input; otherwise click the mapped send element. Fallback: submit nearest form.
- MutationObserver lifespan: create before triggering send; disconnect ~800ms after send (like validate).
- Audit: best‑effort — even if `observed` is null, still append `events.log` with context.

Acceptance (manual)
- Relay page (`/playground/relay.html`): Map Seminar (left) → popup “Send Text: HELLO” → left history shows HELLO; right mirrors (toggle on). `out/audit.json` gains `web_bridge_event` entries.
- WA/TG/RC/Slack pages: Map each, then “Send Text: E2E” → visible message and audit entries.

## Next (P2) — Capture UI → Seminar (remote → seminar)

- Content attaches listeners to mapped send action:
  - keydown matching mapped key combo OR click on mapped send button
  - capture text from input; post `bridge.sendText` (which logs MCP `participants.message` + `events.log`)
- Demo on Relay: typing on Remote (right) flows back to Seminar (left) and logs MCP events.

## Later (P3) — Subscribe Seminar → UI (seminar → remote)

- Background subscribes to `/sessions/{id}/stream` (WS/SSE) for `turn_result` events
- Forward non‑self AI turns into mapped UI via `content.forwardText`
- Echo suppression: tag outgoing `events.log` with a short provenance id/hash and drop re‑seen items for ~20s

## Commands (Quick Start)

- Start Playground server:
  - `bash scripts/playground.sh start`
  - Open: `http://127.0.0.1:4400/playground/shell.html`
- Run progressive E2E (Playground only):
  - `bash scripts/pw_playground.sh`
- Optional RC (when needed):
  - `bash scripts/pw_orchestrate.sh env:rc`
  - `bash scripts/seed_rocketchat.sh`
  - `PW_FRESH=1 RC_LOGIN_MODE=api-first bash scripts/pw_orchestrate.sh test:rc`

## References

- Feature Reference: `docs/Owners/Browser_Extension/FEATURE_REFERENCE.md`
- Relay mock: `/playground/relay.html` (maps Seminar ↔ Remote)
- Progressive Suite: `extensions/generic-chat-bridge/tests/e2e/progressive/*.spec.ts`
- Mappings: `extensions/generic-chat-bridge/tests/e2e/mappings/*.json`

## Branch & PR Suggestions (P1)

- Branch: `feat/popup-send-text`
- Commit style:
  - `feat(popup): add send text + mapping status`
  - `feat(background): bridge.sendText → MCP participants.message + events.log`
  - `feat(content): content.sendText synth + observer`
- PR title: `feat(popup): send text + mapping status (duplex foundation)`
- PR body: include manual steps on Relay + `out/audit.json` snippet

---

This doc is the restart point. Next time: implement P1 as specified, validate on Relay, then roll to P2 (capture UI → seminar).
