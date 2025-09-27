/**
 * Docker Readiness Smoke Tests (Optional)
 *
 * Run only when OSS services are up locally via docker-compose.
 * Gate with env RUN_OSS=1 to avoid accidental network in CI.
 *
 * Usage:
 *   # In docker folder: docker compose up -d
 *   # In this folder:
 *   RUN_OSS=1 npx playwright test -c playwright.config.ts docker-readiness.spec.ts
 */

import { test, expect, request } from '@playwright/test';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';

test.describe('Docker OSS Readiness', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run Docker readiness checks');

  test('Rocket.Chat responds on / and /api/info', async () => {
    const ctx = await request.newContext();
    // Poll up to ~60s for service to be ready
    let ok = false; let lastStatus = 0;
    for (let i = 0; i < 30; i++) {
      const r = await ctx.get('http://127.0.0.1:3000/api/info');
      lastStatus = r.status();
      if (lastStatus === 200) { ok = true; break; }
      await new Promise(r => setTimeout(r, 2000));
    }
    expect(ok, `Rocket.Chat /api/info not ready (last status ${lastStatus})`).toBeTruthy();
  });

  test('Zulip responds on /', async () => {
    const ctx = await request.newContext();
    let ok = false; let lastStatus = 0;
    for (let i = 0; i < 30; i++) {
      const r = await ctx.get('http://127.0.0.1:9991');
      lastStatus = r.status();
      if (lastStatus === 200) { ok = true; break; }
      await new Promise(r => setTimeout(r, 2000));
    }
    expect(ok, `Zulip home not ready (last status ${lastStatus})`).toBeTruthy();
  });
});

