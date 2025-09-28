/**
 * BrExt • Profile Persistence E2E
 *
 * Goals
 * - Show that selector profiles are persisted per-origin (chrome.storage.local)
 * - Verify that after reload, Validate works without re-picking
 */

import { test, expect, chromium } from '@playwright/test';
import { playgroundUrl } from './urls';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const BASE_URL = process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400';

test('textarea.html • profile persists across reload', async () => {
  const userDataDir = path.join(process.cwd(), '.pw-chrome-persist');
  try { fs.mkdirSync(userDataDir); } catch {}
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });
  const page = await context.newPage();
  await page.goto(playgroundUrl('textarea.html'));
  await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick));

  // Pick once
  await page.evaluate(() => (window as any).__actcli_bridge.pick());
  await page.click('#composer');
  await page.click('#send');
  await page.click('#history');

  // Validate works
  let res = await page.evaluate(async () => (window as any).__actcli_bridge.validate('PERSIST-1'));
  expect(res?.ok).toBeTruthy();

  // Reload page — profile should still be present for this origin
  await page.reload();
  await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.validate));
  res = await page.evaluate(async () => (window as any).__actcli_bridge.validate('PERSIST-2'));
  expect(res?.ok).toBeTruthy();
  await expect(page.locator('#history .msg').last()).toHaveText(/PERSIST-2/);

  await context.close();
});
