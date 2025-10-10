# Browser Extension — Feature Reference (WIP)

This document is a reference for other ActCLI teams while the Browser Extension is under active development. It summarizes current capabilities, surfaces the message contracts we expose, outlines our Playground for predictable testing, and sketches near‑term expansions so adjacent areas (Semhost, Studio, QA) can plan in parallel.

## What It Does Today

- Element picking (A1)
  - Shadow‑DOM overlay with highlight, tooltip, Escape‑to‑cancel
  - 3‑stage mapping: Input → Send (button or keyboard combo) → History
  - Fixed overlay coordinates; works while scrolled

- Selector engine (A2)
  - ARIA‑first (role="textbox") with stable attribute preference (data‑testid, data‑qa)
  - Pruned CSS fallback; lightweight proximity heuristics
  - Browser tests on scoring; re‑learn path on breakage

- Runtime bridge
  - Validates mapping by synthesizing typing + sending and observing visible history appends (MutationObserver)
  - Keyboard‑based send mapping supported (Enter / Ctrl+Enter / Cmd+Enter), or explicit send button click

- Storage & profiles (A4)
  - Per‑origin profile in `chrome.storage.local`
  - Health checks; import/export; Auto Map (best‑effort heuristics)

- MCP integration (A5, MVP)
  - Semhost advertises `participants.register`, `participants.message`, and `events.log`
  - SSE returns `ok/fault`; events appended to `out/audit.json` as `web_bridge_event`

- **Popup duplex UI (NEW ✅)**
  - **Session Management**: Join/Leave seminar with session ID/URL, display name, avatar
  - **Activity Log**: Rolling log (last ~20 events) with auto-scroll, shows direction and participants
  - **Compose**: Native input field with Enter-to-send, Shift+Enter for newlines
  - **Link Page Setup**: Status chips for Input/Send/History, validation, import/export
  - **Settings**: Semhost URL configuration and persistence

- **Background service worker (NEW ✅)**
  - **Per-origin state store**: participant_id, session_id, display_name, avatar, activity log
  - **Join/Leave flows**: Registers participant via MCP, persists state across sessions
  - **Send functionality**: content.sendText + MCP participants.message + events.log with activity logging
  - **SSE streaming**: Live subscription to /sessions/{id}/stream for real-time activity updates

- Playground (A6)
  - Rich local mocks: Textarea, Contenteditable, Minimal (input‑only), Virtualized, Same‑origin Iframe
  - Messenger‑like: WhatsApp‑like, Telegram‑like, Rocket.Chat‑like (class mutation toggle)
  - Productivity‑like: Preply‑like (board + chat)
  - Slack‑like: main channel + thread pane
  - Shell UI with sidebar navigation (`/playground/shell.html`)
  - **Relay page**: Dual chat for seminar ↔ remote mirroring (NEW ✅)

- Progressive Playwright tests
  - Deterministic mapping via `content.injectProfile` / `postMessage` (no overlay clicks)
  - Suite order: Basic → Messenger → Preply → Slack threads
  - Base URL `/playground`; headless toggle available for CI

## What's Coming Next (Short‑Term)

- ~~Popup "Send Text" and Mapping Status~~ **✅ COMPLETED**
  - ~~Popup: input field + button to send an arbitrary message through the mapped page~~ ✅
  - ~~Background: `bridge.sendText` → invokes `content.sendText` (synthesize keys/click), logs MCP `participants.message` + `events.log`~~ ✅
  - ~~Content: `content.sendText` mirrors validate flow but without typing the full payload into history observation only; returns `{ ok, observed }`~~ ✅
  - ~~Mapping status: show input selector, send (button or captured key combo), history selector; run Health on popup open~~ ✅

- **Page-to-seminar capture (HIGH PRIORITY)**
  - Detect user sends on linked page and post them to seminar automatically
  - Loop suppression and bidirectional forwarding toggles
  - "Forward to Page" / "Listen from Page" toggle controls in popup

- **Session listing UI (MEDIUM PRIORITY)**
  - Add session picker for Local/Recent sessions if sessions.list endpoint is available
  - Recent session history and quick-join functionality

- Selector engine unit tests (A2 deepening)
  - Label proximity weighting ("Send", "Reply")
  - Stable attributes scoring (data‑qa > class), ARIA‑first confirmations
  - Mutation toggles across mocks confirm re‑learn triggers (no silent failure)

- Optional: RC orchestration wrapper
  - `scripts/rc.sh` with `up/down/status/logs/seed` to simplify live RC smoke when desired

## Message Contracts (Internal)

- Content (page context)
  - `content.picker.start` — start overlay; user clicks 3 elements
  - `content.health` — returns `{ ok: boolean }` (input + history resolved; send optional)
  - `content.validate` — `{ text }` → synthesizes typing + send; observes history; returns `{ ok, observed }`
  - `content.injectProfile` — `{ profile }` → set `{ input, send, history }` directly (no overlay)
  - `content.autoMap` — heuristic profile for common UIs (best‑effort)
  - **`content.sendText`** — **✅ IMPLEMENTED** — identical to validate flow, used for actual message sending
  - **`content.forwardText`** — **✅ IMPLEMENTED** — mirrors sendText for seminar→page forwarding

- Background (service worker)
  - `bridge.saveProfile` / `bridge.getProfile` / `bridge.deleteProfile`
  - `bridge.pickStart` → proxy to content
  - `bridge.validate` → proxy to content; logs `events.log` to MCP
  - **`bridge.join` / `bridge.leave`** — **✅ IMPLEMENTED** — session management with participant registration
  - **`bridge.sendText`** — **✅ IMPLEMENTED** — calls `participants.message` + `events.log`; proxies to content.sendText
  - **`bridge.subscribe.start` / `bridge.subscribe.stop`** — **✅ IMPLEMENTED** — SSE streaming for live activity
  - **`bridge.state.get` / `bridge.state.set`** — **✅ IMPLEMENTED** — per-origin state management
  - **`bridge.activity.get`** — **✅ IMPLEMENTED** — retrieve activity log for popup display
  - **`config.get` / `config.set`** — **✅ IMPLEMENTED** — semhost URL configuration

- Semhost MCP tools
  - `participants.register` — `{ origin, display_name, participant_id, capabilities }`
  - `participants.message` — `{ participant_id, text, origin }`
  - `events.log` — `{ event, origin, participant_id?, data? }`

## Playground Index

- `/playground/index.html` — landing page with links & tips
- `/playground/shell.html` — left sidebar with iframe (no back/forward needed)
- Pages for mapping:
  - `textarea.html`, `contenteditable.html`, `minimal.html`, `virtualized.html`, `iframe.html`
  - `wa.html` (WhatsApp‑like), `tg.html` (Telegram‑like), `rc.html` (Rocket.Chat‑like, mutation toggle)
  - `preply.html` (board + chat), `slack.html` (threads)
  - (New) `relay.html` (dual chat, seminar ↔ remote mirroring)

## Integration Guidance for Other Teams

- Semhost / Evidence (A5)
  - Consume `events.log` entries for provenance in session audit (`web_bridge_event` with origin/selectors/timestamps)
  - Uniform participant interface: Web participants treated same as model adapters (no special‑casing)

- Studio (UI)
  - Experimental flag to enable "Web UI participant" and show mapping status
  - Show audit warnings and ToS disclaimers prior to enabling web bridge features

- QA
  - Use Progressive Suite to validate bridge against mocks
  - Add new mocks by cloning existing pages and tweaking selectors; supply mapping JSON under `tests/e2e/mappings/`

## Roadmap (Sketched)

- ~~MVP demo: Popup "Send Text" → map any Playground page → send and audit OK~~ **✅ COMPLETED**
- **Live local demo**: Two browser instances with Ollama → full duplex seminar participation without cloud dependencies
- **Page capture**: Automatic detection and forwarding of user messages from linked pages to seminar
- Live RC/Zulip smoke (opt‑in): only after RC login pains are fully tamed or bypassed via API token in UI flows
- Selector resilience: richer scoring and structured tests; re‑learn prompts

## How to Try It (NEW ✅)

1. **Set Semhost URL** in Settings if needed (defaults to `http://127.0.0.1:7530`)
2. **Enter Session ID/URL**, Display Name, and optional Avatar, then **Join Seminar**
3. **Watch Activity** update as turns come in from other participants
4. **Type in Compose** and press Send to contribute to the seminar
5. **Optional**: Link Page (Setup) to mirror sends into a chat UI — Pick Page Controls → Check Link → Validate
6. **Compose still works** even without linking a page — popup is the primary interface

---

Contact: Codex‑BrExt (implementation), Claude‑BrExt (validation)

