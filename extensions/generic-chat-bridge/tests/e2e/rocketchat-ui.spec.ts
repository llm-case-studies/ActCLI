/**
 * Rocket.Chat UI E2E (Optional, gated by RUN_OSS=1)
 *
 * Preconditions
 * - Docker services up: see docker/README.md
 * - Seed script executed to create users/channel:
 *     node ../../docker/seed-rocketchat.mjs
 * - ENV: RUN_OSS=1 to enable this test
 *
 * Flow
 * - Login as alice
 * - Navigate to #e2e channel
 * - Use overlay picker to learn input/send/history selectors
 * - Validate sending a message and assert it appears in history
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';
const RC_USER = process.env.RC_USER1 || 'alice';
const RC_PASS = process.env.RC_USER1_PASS || 'alicepass';
const RC_CHANNEL = process.env.RC_CHANNEL || 'e2e';

test.describe('Rocket.Chat UI (optional)', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run Rocket.Chat UI test');

  test('pick → validate in #e2e', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-rc');
    try { fs.mkdirSync(userDataDir); } catch {}
    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    const page = await context.newPage();

    // Login page
    await page.goto(`${RC_BASE}/login`);
    // Fill username/email and password robustly
    await page.fill('input[name="emailOrUsername"], input[type="email"], input[placeholder*="Username" i]', RC_USER);
    await page.fill('input[name="pass"], input[type="password"]', RC_PASS);
    // Click the submit/login button
    const loginBtn = page.getByRole('button', { name: /login|sign in/i }).first();
    if (await loginBtn.count()) {
      await loginBtn.click();
    } else {
      await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');
    }

    // Wait for home UI to load; open channel
    await page.waitForLoadState('domcontentloaded');
    // Try direct channel URL if UI selectors vary
    await page.goto(`${RC_BASE}/channel/${encodeURIComponent(RC_CHANNEL)}`);

    // Wait for the debug API to be available in MAIN world
    await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick));

    // Teach selectors: input → send → history
    await page.evaluate(() => (window as any).__actcli_bridge.pick());
    // Input: prefer role=textbox or contenteditable
    const inputCand = page.locator('[role="textbox"], [contenteditable="true"], textarea');
    await expect(inputCand.first()).toBeVisible({ timeout: 10000 });
    await inputCand.first().click();
    // Send: try role=button name~send, fallback to common data-qa
    const sendCand = page.getByRole('button', { name: /send/i }).or(page.locator('[data-qa*="send" i]')); 
    await expect(sendCand.first()).toBeVisible({ timeout: 10000 });
    await sendCand.first().click();
    // History: look for role=list or message container
    const histCand = page.locator('[role="list"], [data-qa*="message" i], .messages-box');
    await expect(histCand.first()).toBeVisible({ timeout: 10000 });
    await histCand.first().click();

    // Validate
    const text = 'RC-E2E '+Date.now();
    const res = await page.evaluate(async (t) => (window as any).__actcli_bridge.validate(t), text);
    expect(res?.ok).toBeTruthy();

    // Assert message appears — search within history area
    await expect(page.locator(`text=${text}`)).toBeVisible({ timeout: 10000 });

    await context.close();
  });
});

