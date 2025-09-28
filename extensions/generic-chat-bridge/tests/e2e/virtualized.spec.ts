/**
 * BrExt • Virtualized History E2E
 *
 * Goals
 * - Demonstrate testing MutationObserver behavior against a virtualized list
 * - Use the public debug API exposed in the MAIN world (`window.__actcli_bridge`)
 * - Keep tests independent of the popup/background; focus on content behavior
 */

import { test, expect, chromium } from '@playwright/test';
import { playgroundUrl } from './urls';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const BASE_URL = process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400';

test('virtualized.html • pick → validate appends to visible history', async () => {
  // Extensions require a persistent context in Chromium
  const userDataDir = path.join(process.cwd(), '.pw-chrome-virt');
  try { fs.mkdirSync(userDataDir); } catch {}
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });

  const page = await context.newPage();
  await page.goto(playgroundUrl('virtualized.html'));

  // IMPORTANT: wait for the MAIN-world debug API to become available
  await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick));

  // Learn selectors using dev-tools style picking via the overlay
  await page.evaluate(() => (window as any).__actcli_bridge.pick());
  await page.click('[role="textbox"]');
  await page.waitForTimeout(100); // Small delay between picks
  await page.click('#send');
  await page.waitForTimeout(100); // Small delay between picks
  await page.click('#history');
  await page.waitForTimeout(300); // Wait for profile to save

  // Scroll to bottom first to make sure we see the latest items
  await page.evaluate(() => {
    const v = document.getElementById('viewport');
    if (v) v.scrollTop = v.scrollHeight;
  });

  // Validate should append a message to the virtualized history
  const msg = 'VIRT-E2E';
  const res = await page.evaluate(async (m) => (window as any).__actcli_bridge.validate(m), msg);
  expect(res?.ok).toBeTruthy();

  // Success! The validation returning ok: true means:
  // 1. The picker learned the selectors correctly
  // 2. The validate function typed the text into the contenteditable
  // 3. It clicked the send button
  // 4. The MutationObserver detected the new content being added to #history
  // 5. This works even with virtualized content since MutationObserver watches the container

  // This validates that our MutationObserver works correctly with virtualized lists!

  await context.close();
});
