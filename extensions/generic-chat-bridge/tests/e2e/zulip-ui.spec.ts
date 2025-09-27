/**
 * Zulip UI E2E (Optional, gated by RUN_OSS=1 and ZULIP_SEEDED=1)
 *
 * Preconditions
 * - Docker Zulip running (see docker/README.md)
 * - Initial setup completed via web UI (realm + admin)
 * - Seeded via: `ZULIP_EMAIL=... ZULIP_API_KEY=... node ../../docker/seed-zulip.mjs`
 * - ENV: RUN_OSS=1 ZULIP_SEEDED=1 to enable this test
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const ZULIP_SEEDED = process.env.ZULIP_SEEDED === '1' || process.env.ZULIP_SEEDED === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const Z_SITE = process.env.ZULIP_SITE || 'http://127.0.0.1:9991';
const Z_USER = process.env.ZULIP_USER1_EMAIL || 'alice@local';
const Z_PASS = process.env.ZULIP_USER1_PASS || 'alicepass';
const Z_STREAM = process.env.ZULIP_STREAM || 'e2e';

test.describe('Zulip UI (optional)', () => {
  test.skip(!(RUN_OSS && ZULIP_SEEDED), 'Set RUN_OSS=1 ZULIP_SEEDED=1 to run Zulip UI test');

  test('pick → validate in stream', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-zulip');
    try { fs.mkdirSync(userDataDir); } catch {}
    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    const page = await context.newPage();

    // Login form
    await page.goto(`${Z_SITE}/login/`);
    await page.fill('input[type="email"], input[name="username"]', Z_USER);
    await page.fill('input[type="password"]', Z_PASS);
    await page.click('text=/Sign in|Log in/i, button[type="submit"]');

    // Wait for app shell
    await page.waitForLoadState('domcontentloaded');
    // Try to open the stream via left sidebar filter or search
    // Fallback: open All messages then use quick nav
    await page.goto(`${Z_SITE}`);
    // Attempt to click stream link by name
    const streamLink = page.locator(`a:has-text("${Z_STREAM}")`).first();
    if (await streamLink.count()) {
      await streamLink.click();
    }

    // Wait for MAIN-world debug API
    await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick));

    // Teach selectors: input → send → history
    await page.evaluate(() => (window as any).__actcli_bridge.pick());
    // Compose area: contenteditable textbox
    const inputCand = page.locator('[role="textbox"], [contenteditable="true"]');
    await expect(inputCand.first()).toBeVisible({ timeout: 15000 });
    await inputCand.first().click();
    // Send button: look for title or aria-label
    const sendCand = page.locator('[title*="Send" i], [aria-label*="Send" i], button:has-text("Send")');
    await expect(sendCand.first()).toBeVisible({ timeout: 15000 });
    await sendCand.first().click();
    // History container: main feed
    const histCand = page.locator('#message_feed_container, [role="main"], .message_feed');
    await expect(histCand.first()).toBeVisible({ timeout: 15000 });
    await histCand.first().click();

    // Validate
    const text = 'ZULIP-E2E '+Date.now();
    const res = await page.evaluate(async (t) => (window as any).__actcli_bridge.validate(t), text);
    expect(res?.ok).toBeTruthy();
    await expect(page.locator(`text=${text}`)).toBeVisible({ timeout: 15000 });

    await context.close();
  });
});

