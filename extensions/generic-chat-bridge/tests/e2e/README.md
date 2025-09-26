Playwright E2E (BrExt → Playground)

Prereqs
- Node 20+, `npx playwright install chromium`
- Semhost running (optional, for MCP logs): `http://127.0.0.1:7530`
- Static server for playground:
  - From `extensions/generic-chat-bridge/`: `python -m http.server 4400`

Run Locally
1) Set env: `export EXTENSION_PATH=$(pwd)` (the extension root)
2) In this folder: `npx playwright test -c playwright.config.ts`

What Tests Do
- Launch Chromium with the extension loaded (MV3)
- Navigate to `textarea.html` and `contenteditable.html`
- Use debug API exposed by content script to Pick and Validate
- Assert message appended to history

Notes
- Tests use a persistent context to allow MV3 extension loading.
- Popup not used; we drive content script helper `window.__actcli_bridge`.
- For virtualized/iframe cases, copy/extend the existing test patterns.

