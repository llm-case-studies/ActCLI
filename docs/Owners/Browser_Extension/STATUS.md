Browser Extension — Sprint 1 Kickoff (Codex-BrExt)

Summary
- Added minimal, ToS-safe extension scaffold under `extensions/generic-chat-bridge/`.
- Implements: manifest (MV3), background (storage + messaging), content overlay (picker), popup UI, and local playground pages (`textarea.html`, `contenteditable.html`).
- Scope intentionally OSS/local only; no provider-specific logic, no backend coupling yet.

How To Try
- Load unpacked: chrome://extensions → Load `extensions/generic-chat-bridge/`.
- Open `extensions/generic-chat-bridge/playground/textarea.html` in a tab.
- Use popup: Pick Elements → Validate. Expect a new history entry.

Planned Next
- Selector scoring tests (A2) and minor resilience improvements.
- Add `virtualized.html` and `iframe.html` playground pages.
- Define MCP shapes for `participants.register`, `participants.message`, `events.log` (Semhost side) and wire background stub when ready.
- Evidence integration plan (append provenance to audit.json via MCP once available).

Notes
- Aligns with Implementation Guide (A1/A2 kickoff) and respects the ToS research gate by sticking to OSS/local testing.

