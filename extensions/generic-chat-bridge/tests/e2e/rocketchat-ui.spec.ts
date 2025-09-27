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

import { test, expect, chromium, request } from '@playwright/test';
import { loadDotEnv } from './env';
import path from 'path';
import fs from 'fs';

// Load env from docker/.env if present (and not already set)
loadDotEnv();

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';
// Prefer seeded user creds; fall back to admin creds from .env; finally hard default
const RC_USER = process.env.RC_USER1 || process.env.RC_ADMIN_EMAIL || 'alice';
const RC_PASS = process.env.RC_USER1_PASS || process.env.RC_ADMIN_PASS || 'alicepass';
const RC_CHANNEL = process.env.RC_CHANNEL || 'e2e';
const RC_LOGIN_MODE = process.env.RC_LOGIN_MODE || 'api-first'; // 'api', 'ui', 'api-first'
const RC_CLEAR_STORAGE = process.env.RC_CLEAR_STORAGE === '1' || process.env.RC_CLEAR_STORAGE === 'true';

test.describe('Rocket.Chat UI (optional)', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run Rocket.Chat UI test');

  test('pick → validate in #e2e', async () => {
    test.setTimeout(120000); // allow extra time for pacing/mapping
    const baseDir = path.join(process.cwd(), '.pw-chrome-rc');
    const FRESH = process.env.PW_FRESH === '1' || process.env.PW_FRESH === 'true';
    const userDataDir = FRESH ? `${baseDir}-${Date.now()}` : baseDir;
    try { fs.mkdirSync(userDataDir); } catch {}
    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    // Clear cookies proactively as well
    await context.clearCookies();
    const page = await context.newPage();
    // Capture console and page errors to aid debugging
    page.on('console', msg => console.log('[RC PAGE]', msg.type(), msg.text()));
    page.on('pageerror', err => console.log('[RC ERROR]', err.message));

    // Prefer API login for stability; fall back to UI if configured
    let apiLogged = false;
    if (RC_LOGIN_MODE !== 'ui') {
      try {
        const rc = await request.newContext();
        const r = await rc.post(`${RC_BASE}/api/v1/login`, {
          data: { user: RC_USER, password: RC_PASS },
          timeout: 10000,
        });
        if (r.ok()) {
          const j = await r.json();
          const token = j?.data?.authToken;
          const userId = j?.data?.userId;
          if (token && userId) {
            const host = new URL(RC_BASE).hostname;
            await context.addCookies([
              { name: 'rc_token', value: String(token), domain: host, path: '/' },
              { name: 'rc_uid', value: String(userId), domain: host, path: '/' },
            ]);
            await context.addInitScript((uid, tok) => {
              try {
                localStorage.setItem('Meteor.userId', uid);
                localStorage.setItem('Meteor.loginToken', tok);
                const exp = new Date(Date.now() + 24*3600*1000).toISOString();
                localStorage.setItem('Meteor.loginTokenExpires', exp);
              } catch {}
            }, userId, token);
            apiLogged = true;
            console.log('[RC LOGIN] API login OK');
          }
        }
      } catch (e) {
        console.log('[RC LOGIN] API login error:', String(e));
      }
      if (!apiLogged && RC_LOGIN_MODE === 'api') {
        throw new Error('RC_LOGIN_MODE=api but API login failed');
      }
    }

    if (!apiLogged) {
      // UI login path (human-like)
      await page.goto(`${RC_BASE}/login`, { waitUntil: 'domcontentloaded' });
      console.log('[RC LOGIN] Navigated to login page');
      if (RC_CLEAR_STORAGE) {
        // Optional: Clear site storage to avoid auto-login residues
        await page.evaluate(async () => {
          try { localStorage.clear(); sessionStorage.clear(); } catch {}
          try { if ('caches' in window) { const keys = await caches.keys(); await Promise.all(keys.map(k => caches.delete(k))); } } catch {}
          try {
            const anyIDB: any = indexedDB as any;
            const dbs = (await anyIDB.databases?.()) || [];
            await Promise.all(dbs.map((d: any) => new Promise((res) => { const req = indexedDB.deleteDatabase(d.name); req.onsuccess = req.onerror = req.onblocked = () => res(true); })));
          } catch {}
        });
      }
      await page.waitForTimeout(400);

      // Find fields
      const userField = page.getByLabel(/email|username/i).or(page.getByPlaceholder(/example@|username/i)).or(page.locator('input[name="emailOrUsername"], input[type="email"]'));
      const passField = page.getByLabel(/password/i).or(page.locator('input[name="pass"], input[type="password"]'));
      await expect(userField.first()).toBeVisible({ timeout: 15000 });
      await expect(passField.first()).toBeVisible({ timeout: 15000 });
      // Human-like typing and commit
      await passField.first().click();
      await page.waitForTimeout(200);
      await userField.first().click();
      await page.keyboard.type(RC_USER, { delay: 70 });
      await passField.first().click();
      await page.keyboard.type(RC_PASS, { delay: 80 });
      await page.keyboard.press('Tab');
      const form = page.locator('form');
      if (await form.count()) { try { await form.first().click({ position: { x: 8, y: 8 } }); } catch {} }
      await page.waitForTimeout(250);
      const loginBtn = page.getByRole('button', { name: /login|sign in/i }).first();
      if (await loginBtn.count()) {
        await expect(loginBtn).toBeEnabled({ timeout: 5000 }).catch(() => {});
        await loginBtn.click();
      } else {
        await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');
      }
    }

    // Probe for login success: navigate to channel; if redirected back to /login, fail early with context
    await page.waitForLoadState('domcontentloaded', { timeout: 10000 });
    await page.goto(`${RC_BASE}/channel/${encodeURIComponent(RC_CHANNEL)}`);
    // Small settle window
    await page.waitForTimeout(800);
    // Robust login detection: URL check, role-based, and body text + password input
    const loginVisible = page.url().includes('/login')
      || (await page.getByRole('heading', { name: /login/i }).count()) > 0
      || (await page.getByRole('button', { name: /login/i }).count()) > 0
      || (await page.locator('input[type="password"], input[name="pass"]').count()) > 0
      || (await page.evaluate(() => /\bLogin\b/i.test(document.body?.innerText || '')));
    if (loginVisible) {
      // Persist a small status file and screenshot for Claude
      const errText = await page.locator('[role="alert"], .rcx-notification').first().textContent().catch(() => '');
      const status = { url: page.url(), title: await page.title(), loginVisible: true, error: (errText || '').trim() };
      const fs2 = await import('fs');
      fs2.writeFileSync('rocketchat-login-status.json', JSON.stringify(status, null, 2));
      await page.screenshot({ path: 'rocketchat-login-failed.png', fullPage: true });
      throw new Error(`Rocket.Chat login failed (login UI detected). See rocketchat-login-status.json and screenshot.\n`);
    }
    // Write a status marker on success as well
    {
      const fs2 = await import('fs');
      const status = { url: page.url(), title: await page.title(), loginVisible: false };
      fs2.writeFileSync('rocketchat-login-status.json', JSON.stringify(status, null, 2));
    }

    // Wait for the debug API to be available in MAIN world
    await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick));

    // Reuse mapping if present, otherwise overlay-pick as fallback
    const fs = await import('fs');
    const p = path.resolve(__dirname, 'mappings/rocketchat.json');
    if (fs.existsSync(p)) {
      const mapping = JSON.parse(fs.readFileSync(p, 'utf-8')) as { input: string; send?: string; history: string };
      await page.evaluate((m) => {
        window.postMessage({ __actcli_pick: true, stage: 'input', selector: m.input }, '*');
        window.postMessage({ __actcli_pick: true, stage: 'send', selector: m.send || '__ENTER__' }, '*');
        window.postMessage({ __actcli_pick: true, stage: 'history', selector: m.history }, '*');
      }, mapping);
    } else {
      // Teach selectors via overlay: input → send → history
      await page.evaluate(() => (window as any).__actcli_bridge.pick());
      // Input: prefer role=textbox or contenteditable
      const inputCand = page.locator('[role="textbox"], [contenteditable="true"], textarea');
      await expect(inputCand.first()).toBeVisible({ timeout: 10000 });
      await inputCand.first().click();
      // Send: try role=button name~send, fallback to Enter (skip)
      const sendBtn = page.getByRole('button', { name: /send/i }).first();
      if (await sendBtn.count()) {
        await sendBtn.click();
      } else {
        await page.keyboard.press('Enter'); // skip send stage
      }
      // History: look for role=list or message container
      const histCand = page.locator('[role="list"], [data-qa*="message" i], .messages-box');
      await expect(histCand.first()).toBeVisible({ timeout: 10000 });
      await histCand.first().click();
    }

    // Validate
    const text = 'RC-E2E '+Date.now();
    const res = await page.evaluate(async (t) => (window as any).__actcli_bridge.validate(t), text);
    expect(res?.ok).toBeTruthy();

    // Assert message appears — search within history area
    await expect(page.locator(`text=${text}`)).toBeVisible({ timeout: 10000 });

    await page.screenshot({ path: 'rocketchat-channel.png', fullPage: true }).catch(() => {});
    await context.close();
  });
});
