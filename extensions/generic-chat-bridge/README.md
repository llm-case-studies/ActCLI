ActCLI Web Chat Bridge (Experimental)

Overview
- Purpose: Human collaboration bridge to let actuaries join ActCLI seminars from any web chat UI.
- Scope: Element picker + selector profiles (per-origin), validate flow, storage. No provider-specific automation.
- Integration: Future MCP calls to Semhost for participants.register/participants.message/events.log.

Status
- MVP scaffolding only: manifest, popup, background, content overlay, and local playground pages.
- ToS safety: OSS-only testing; no references to proprietary chat providers.

Load Unpacked
1) Open chrome://extensions → Enable Developer Mode
2) Load unpacked → select `extensions/generic-chat-bridge/`
3) Open a test page (see `playground/`) and click the extension icon.

Basic Flow
- Pick Elements: Click input → send → history.
- Validate: Simulates typing and send; observes history append.
- Profiles: Stored per-origin via `chrome.storage.local`.
 - MCP: Configure Semhost URL in popup and actions will POST to `/mcp/rpc` and briefly stream `/mcp/sse` to finalize jobs (events logged to `out/audit.json`).

Playground
- Start a static server or open the files directly:
  - `playground/textarea.html`
  - `playground/contenteditable.html`
  - `playground/virtualized.html`
  - `playground/iframe.html`

Selector Engine Tests (A2)
- Open `tests/selectors.spec.html` in a browser. The page reports PASS/FAIL for core heuristics.
- No dependencies; runs entirely client-side.

Semhost Integration (A5)
- Tools advertised: `participants.register`, `participants.message`, `events.log`.
- Connect: Registers a participant with generated id and logs an event.
- Validate: Logs an `events.log` record including whether a history append was observed.

Playwright Tips (PW Mastery)
- Always use a persistent Chromium context to load MV3 extensions; keep `headless: false`.
- Serve Playground via HTTP (not file://): `python -m http.server 4400` → `http://127.0.0.1:4400`.
- Set `EXTENSION_PATH` to the absolute path of this folder (contains `manifest.json`).
- Wait for the MAIN‑world debug API before interacting:
  - `await page.waitForFunction(() => Boolean(window.__actcli_bridge?.pick))`.
- Prefer driving flows via the MAIN‑world debug API to avoid popup interactions.
- For iframes, use `frameLocator` and call the API in the frame’s page context.
- Capture console/page errors to accelerate debugging:
  - `page.on('console', ...)` and `page.on('pageerror', ...)`.
- If environments are slow, bump timeout: `--timeout=60000` or per‑step waits.
- Clear stale profiles: delete `.pw-chrome-profile*` in `tests/e2e/` before re‑runs.
- See `tests/e2e/README.md` for full troubleshooting and examples.

Notes
- This is plain JS/HTML; no bundler required. Keep permissions minimal.
- The code intentionally avoids background automation and respects human-paced usage.
