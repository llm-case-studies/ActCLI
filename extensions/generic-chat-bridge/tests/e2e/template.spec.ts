/**
 * Playwright Template Spec — MV3 Extension + Page Flow
 *
 * Copy this file to start a new E2E. It demonstrates best practices for
 * testing a Manifest V3 extension that exposes a MAIN‑world debug API
 * (see `window.__actcli_bridge`), without relying on the popup UI.
 */

import { test, expect, chromium } from '@playwright/test';
import { playgroundUrl } from './urls';
import path from 'path';
import fs from 'fs';

// Required: EXTENSION_PATH should point to the extension root (with manifest.json)
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
// Optional: where your test page is hosted (serve via `python -m http.server 4400`)
const BASE_URL = process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400';

test('TEMPLATE • pick → validate on a page', async () => {
  // 1) Launch a persistent context so Chromium can load the MV3 extension
  const userDataDir = path.join(process.cwd(), '.pw-chrome-template');
  try { fs.mkdirSync(userDataDir); } catch {}
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false, // MV3 requires a visible browser for extensions
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });

  // 2) Create a page and navigate to a test URL
  const page = await context.newPage();
  await page.goto(playgroundUrl('textarea.html')); // change to your target page

  // 3) OPTIONAL: capture logs to speed up debugging
  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  // 4) Wait for the MAIN‑world debug API to be available before driving the flow
  await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick));

  // 5) Pick elements via overlay — input → send → history
  await page.evaluate(() => (window as any).__actcli_bridge.pick());
  await page.click('#composer'); // input
  await page.waitForTimeout(100); // Small delay between picks
  await page.click('#send');     // send button
  await page.waitForTimeout(100); // Small delay between picks
  await page.click('#history');  // history container
  await page.waitForTimeout(300); // Wait for profile to save

  // 6) Validate — simulates typing + clicking send, observes MutationObserver
  const message = 'TEMPLATE-E2E';
  const res = await page.evaluate(async (m) => (window as any).__actcli_bridge.validate(m), message);
  expect(res?.ok).toBeTruthy();

  // 7) Assert the new message is visible in history
  await expect(page.locator('#history .msg').last()).toHaveText(new RegExp(message));

  // 8) Clean up
  await context.close();
});
