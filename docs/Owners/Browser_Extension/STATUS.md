Browser Extension — Sprint 1 Kickoff (Codex-BrExt)

Summary
- Added minimal, ToS-safe extension scaffold under `extensions/generic-chat-bridge/`.
- Implements: manifest (MV3), background (storage + messaging), content overlay (picker with Esc-cancel), popup UI, and local playground pages (`textarea.html`, `contenteditable.html`, `virtualized.html`, `iframe.html`).
- Popup now includes Health check and Import/Export of per-origin profiles.
- Scope intentionally OSS/local only; no provider-specific logic, no backend coupling yet.
- Semhost now advertises MCP tools for the bridge: `participants.register`, `participants.message`, `events.log` (SSE replies with ok + audit append).

Sprint 2 (A6/A7) Scaffolding
- Playwright E2E setup under `extensions/generic-chat-bridge/tests/e2e/` with config and specs (uses content debug API `__actcli_bridge`).
- Docker targets for OSS chat (Rocket.Chat, Zulip) under `extensions/generic-chat-bridge/docker/` with README.
- Docs: install, usage, and test-matrix under `extensions/generic-chat-bridge/docs/`.

Next (Claude-BrExt)
- Run Playwright against Playground (`python -m http.server 4400`) with the extension loaded (`EXTENSION_PATH=` env), confirm green.
- Spin Docker targets, perform manual triad scenario, collect audit.json and screenshots for PR.

How To Try
- Load unpacked: chrome://extensions → Load `extensions/generic-chat-bridge/`.
- Open `extensions/generic-chat-bridge/playground/textarea.html` in a tab.
- Use popup: Pick Elements → Validate. Expect a new history entry.

Planned Next
- Selector scoring tests (A2) and minor resilience improvements (label proximity, stable attrs weighting).
- Options page for Semhost URL; stub MCP calls in background for local-only dev.
- Define MCP shapes for `participants.register`, `participants.message`, `events.log` (Semhost side) and wire background stub when ready.
- Evidence integration plan (append provenance to audit.json via MCP once available).

Notes
- Aligns with Implementation Guide (A1/A2 kickoff) and respects the ToS research gate by sticking to OSS/local testing.
