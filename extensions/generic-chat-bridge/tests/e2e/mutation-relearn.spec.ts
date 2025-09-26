/**
 * BrExt • Mutation / Re-learn E2E
 *
 * Goals
 * - Simulate DOM mutation that breaks a stored selector
 * - Verify Validate fails with a clear error
 * - Trigger re-learning (Pick) and then Validate succeeds
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const BASE_URL = process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400';

test('textarea.html • mutation breakage then re-learn', async () => {
  const userDataDir = path.join(process.cwd(), '.pw-chrome-mutate');
  try { fs.mkdirSync(userDataDir); } catch {}
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });
  const page = await context.newPage();
  await page.goto(`${BASE_URL}/textarea.html`);
  await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick));

  // Initial learn
  await page.evaluate(() => (window as any).__actcli_bridge.pick());
  await page.click('#composer');
  await page.waitForTimeout(100); // Small delay between picks
  await page.click('#send');
  await page.waitForTimeout(100); // Small delay between picks
  await page.click('#history');
  await page.waitForTimeout(300); // Wait for profile to save
  let res = await page.evaluate(async () => (window as any).__actcli_bridge.validate('MUT-1'));
  expect(res?.ok).toBeTruthy();

  // Mutate DOM to break the send button selector (rename id)
  await page.evaluate(() => {
    const send = document.getElementById('send');
    if (send) send.id = 'send-broken';
  });

  // Validate should now fail with elements-not-found
  res = await page.evaluate(async () => (window as any).__actcli_bridge.validate('MUT-FAIL'));
  expect(res?.ok).toBeFalsy();
  expect(res?.error).toMatch(/elements-not-found|no-profile/i);

  // Re-learn with new selector
  await page.evaluate(() => (window as any).__actcli_bridge.pick());
  await page.click('#composer');
  await page.waitForTimeout(100); // Small delay between picks
  await page.click('#send-broken');
  await page.waitForTimeout(100); // Small delay between picks
  await page.click('#history');
  await page.waitForTimeout(300); // Wait for profile to save

  res = await page.evaluate(async () => (window as any).__actcli_bridge.validate('MUT-2'));
  expect(res?.ok).toBeTruthy();
  await expect(page.locator('#history .msg').last()).toHaveText(/MUT-2/);

  await context.close();
});

