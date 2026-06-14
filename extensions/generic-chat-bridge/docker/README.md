OSS Targets (Rocket.Chat + Zulip)

This compose spins up local OSS chat servers for E2E runs. Intended for CI/dev only.

Recollection Note
- This stack is a test harness for the ActCLI generic inter-chat extension. Rocket.Chat and Zulip stand in for Slack/Telegram-like chat surfaces so the browser extension can learn selectors, send messages, and validate history reads without touching real third-party chat accounts.
- It is not product infrastructure and is not part of iLegalFlow. If found running on a workstation, treat it as a revivable lab fixture, not a required service.
- The MSI instance inspected on 2026-06-14 had tiny seeded/test data only: users `alexsudakov`, `bob`, and `rocket.cat`; rooms `general`, `e2e`, and DMs; 18 total messages. Recent June 2026 entries were Rocket.Chat update notices, not human chat.
- Zulip was restart-looping because `ZULIP_ADMINISTRATOR` was not configured. Rocket.Chat was still reachable on LAN port 3000 because the compose file exposed `3000:3000` and used `restart: unless-stopped`.

Revival Checklist
- Start only when actively testing the chat bridge.
- Prefer localhost-only port binds, for example `127.0.0.1:3000:3000` and `127.0.0.1:9991:9991`, unless a LAN browser/device test explicitly needs exposure.
- Keep Docker volumes if preserving old seeded state matters; use `docker compose down` without `-v`.
- If Zulip is needed, configure the required administrator setting before bringing it up.
- If Rocket.Chat/Mongo report an unhealthy Mongo container while Rocket.Chat works, check the Mongo healthcheck before assuming the database is down.

Usage
- `docker compose up -d` in this folder
- Rocket.Chat: http://localhost:3000 (create users via UI on first run)
- Zulip: http://localhost:9991 (follow setup prompts)

Seeding
- Rocket.Chat: Use UI to create `alice` and `bob` users; create a DM or channel `#e2e`.
- Zulip: Create a realm, then two users; start a stream `e2e`.

BrExt Flow
1) Load the extension in Chromium
2) Open Rocket.Chat or Zulip tab
3) Pick Elements → Validate → Connect
4) Use Semhost to send messages to participant (future A5 streaming)

Caution
- Images are large; not suitable for minimal CI unless cached.
- Security not hardened; dev-only usage.

Seeding (Rocket.Chat)
- Copy `.env.example` to `.env` and review credentials (or export env vars)
- Ensure admin exists (first run requires creating an admin via web UI)
- Seed users/channel via REST:
  - From this folder: `node seed-rocketchat.mjs`
  - Creates `alice` and `bob`, channel `#e2e`, invites users, posts a welcome message
  - Optional: set `RC_USERS=carol:carol@local:carolpass,dave:dave@local:davepass` to create/invite additional users automatically

Playwright UI Spin (optional)
- In tests/e2e:
  - `export EXTENSION_PATH=$(realpath ../../)`
  - `RUN_OSS=1 npx playwright test -c playwright.config.ts rocketchat-ui.spec.ts`
- The test logs in as `alice`, opens `#e2e`, learns selectors via overlay, validates sending a test message.
