OSS Targets (Rocket.Chat + Zulip)

This compose spins up local OSS chat servers for E2E runs. Intended for CI/dev only.

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
