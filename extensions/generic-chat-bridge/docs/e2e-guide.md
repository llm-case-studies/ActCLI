End-to-End Guide (Fresh Session)

Overview
- Validate the MV3 extension on local Playground and optionally against OSS chat servers in Docker.
- Use Playwright for automation; use the main‑world debug API to avoid popup interactions.

Quick Start (Playground)
1) Serve Playground:
   - From `extensions/generic-chat-bridge/`:
     - `python -m http.server 4400`
2) Install PW Chromium:
   - `npx playwright install chromium`
3) Run tests:
   - `cd extensions/generic-chat-bridge/tests/e2e`
   - `export EXTENSION_PATH=$(realpath ../../)`
   - `npx playwright test -c playwright.config.ts`

Manual Sanity (no PW)
- Load extension: chrome://extensions → Developer Mode → Load `extensions/generic-chat-bridge/`
- Open: http://127.0.0.1:4400/textarea.html
- Console:
  - `window.__actcli_bridge.pick()` then click input → send → history
  - `await window.__actcli_bridge.validate('Hello')` (message appears)

Semhost (optional)
- Start Semhost: `python -m uvicorn semhost.main:create_app --factory --host 127.0.0.1 --port 7530`
- Popup → set Semhost URL (default OK). Actions append `web_bridge_event` to `out/audit.json`.

Docker OSS Targets (optional)
1) Start services:
   - `cd extensions/generic-chat-bridge/docker`
   - `docker compose up -d`
2) Seed Rocket.Chat:
   - Ensure admin exists (create via UI on first run)
   - `cp .env.example .env` and adjust credentials as needed
   - `node seed-rocketchat.mjs`
3) Seed Zulip:
   - Complete initial setup in UI; get admin API key
   - `ZULIP_EMAIL=... ZULIP_API_KEY=... node seed-zulip.mjs`

Run OSS Tests (optional)
- Readiness only:
  - `RUN_OSS=1 npx playwright test -c playwright.config.ts docker-readiness.spec.ts`
- Rocket.Chat UI:
  - `RUN_OSS=1 npx playwright test -c playwright.config.ts rocketchat-ui.spec.ts`
- Zulip UI:
  - `RUN_OSS=1 ZULIP_SEEDED=1 npx playwright test -c playwright.config.ts zulip-ui.spec.ts`

Troubleshooting
- 404 from Playground: serve via HTTP (not file://) → `http://127.0.0.1:4400`
- Extension not loading in PW:
  - `EXTENSION_PATH` must be absolute to the folder with `manifest.json`
  - Use persistent context + headless=false (config already sets it)
- Debug API undefined:
  - Tests wait for `window.__actcli_bridge`; increase timeout if slow (`--timeout=60000`)
- Redeclare errors:
  - overlay guards re‑injection; clear `.pw-chrome-profile*` and retry
- Service logs:
  - chrome://extensions → your extension → “Errors”; docker logs for services

Notes for Authors (PW best practices)
- Expose a tiny MAIN‑world debug API to keep tests deterministic
- Avoid popup automation; prefer page‑scoped debug actions
- For frames, use `frameLocator` and evaluate in frame page context
- Capture `page.on('console')` and `page.on('pageerror')` in new specs
- Keep tests network‑light; gate OSS scenarios behind env flags

