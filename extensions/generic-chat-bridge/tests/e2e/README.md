Playwright E2E (BrExt → Playground)

Prereqs
- Node 20+, `npx playwright install chromium`
- Semhost running (optional, for MCP logs): `http://127.0.0.1:7530`
- Static server for playground:
  - From `extensions/generic-chat-bridge/`: `python -m http.server 4400`

Run Locally
1) Set env: `export EXTENSION_PATH=$(pwd)` (the extension root)
2) In this folder: `npx playwright test -c playwright.config.ts`
3) Optional Docker readiness: `RUN_OSS=1 npx playwright test -c playwright.config.ts docker-readiness.spec.ts`
4) Force fresh browser profile (no cached logins): set `PW_FRESH=1`

What Tests Do
- Launch Chromium with the extension loaded (MV3)
- Navigate to `textarea.html` and `contenteditable.html`
- Use debug API exposed by content script to Pick and Validate
- Assert message appended to history

Suggested Additional Specs (included)
- `virtualized.spec.ts` — validate against virtualized history with scrolling
- `iframe.spec.ts` — run inside a same-origin iframe using frameLocator
- `persistence.spec.ts` — confirm profile persistence across reload
- `mutation-relearn.spec.ts` — break a selector, expect failure, re-learn, then succeed
 - Tip: You can bypass overlay picking by injecting a profile directly:
   ```ts
   await page.waitForFunction(() => Boolean((window as any).__actcli_bridge));
   await page.evaluate(() => window.postMessage({ __actcli_pick: true, stage: 'input', selector: '#composer' }, '*'));
   await page.evaluate(() => window.postMessage({ __actcli_pick: true, stage: 'send', selector: '__ENTER__' }, '*'));
   await page.evaluate(() => window.postMessage({ __actcli_pick: true, stage: 'history', selector: '#history' }, '*'));
   // or use the new message API:
   await page.evaluate(() => chrome.runtime.sendMessage({ type: 'content.injectProfile', profile: { input: '#composer', send: '__ENTER__', history: '#history' } }));
   ```

Notes
- Tests use a persistent context to allow MV3 extension loading.
- Popup not used; we drive content script helper `window.__actcli_bridge`.
- For virtualized/iframe cases, copy/extend the existing test patterns.
- To run Docker OSS targets, start services in `extensions/generic-chat-bridge/docker/` with `docker compose up -d`.
- Rocket.Chat UI test loads `docker/.env` automatically if present (without overriding existing env). Set `RC_USER1/RC_USER1_PASS`, or just set `RC_ADMIN_EMAIL/RC_ADMIN_PASS` and the test will use admin creds.
 - To avoid auto-login from a previous run, use `PW_FRESH=1` (deletes the persistent profile dir before launching).

Troubleshooting (PW)
- Extension not loading / globals undefined:
  - Ensure `EXTENSION_PATH` is an absolute path to the extension root that contains `manifest.json`.
  - Example (Linux/macOS): `export EXTENSION_PATH=$(realpath ../../)`
- Using file:// instead of http://:
  - Serve the Playground via HTTP: `python -m http.server 4400` and use `http://127.0.0.1:4400`.
- Race on content scripts:
  - Tests already wait for `window.__actcli_bridge`; if needed, bump timeouts:
    - One‑liner: `npx playwright test -c playwright.config.ts --timeout=60000`
- Stale Chrome profile:
  - Remove `.pw-chrome-profile*` folders in this directory and re‑run tests.
- Service worker/background errors:
  - Open `chrome://extensions`, click the extension → “Errors” to inspect logs.

Progressive Suite
- Location: `progressive/*.spec.ts` with JSON mappings in `mappings/`.
- What it covers:
  - Basic mocks: textarea, contenteditable, minimal, virtualized, iframe
  - Messenger-like: WA/TG/RC (RC includes mutation toggle stress)
  - Productivity-like: Preply (board canvas + chat)
  - Slack-like: main channel + thread pane
- Determinism: tests inject mappings directly (no overlay clicks) via `content.injectProfile` if available, else `window.postMessage` fallback. All tests wait up to ~10s for `window.__actcli_bridge` and capture a screenshot on failure.
- Run the progressive suite:
  - From repo root: `bash scripts/pw_playground.sh`
  - Or here: `EXTENSION_PATH=$(realpath ../../) npx playwright test -c playwright.config.ts progressive`
- Add/inspect mappings:
  - JSON format: `{ "input": "<selector>", "send": "__KEY:Enter__", "history": "<selector>" }`
  - Examples live under `mappings/` (textarea/contenteditable/minimal/virtualized/iframe/wa/tg/rc/preply/slack-main/slack-thread).
  - You can also export/import profiles via the popup UI; tests will always prefer injected mappings for stability.

Orchestration helpers
- `bash scripts/playground.sh start` — start static server at `http://127.0.0.1:4400`
- `bash scripts/pw_playground.sh` — run all Playground E2E (includes progressive)
- `bash scripts/rc.sh up` then `bash scripts/rc.sh seed` — spin up and seed Rocket.Chat
- `PW_FRESH=1 RC_LOGIN_MODE=api-first bash scripts/pw_orchestrate.sh test:rc` — optional RC UI test
