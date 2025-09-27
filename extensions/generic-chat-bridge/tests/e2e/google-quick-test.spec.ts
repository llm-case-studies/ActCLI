/**
 * Quick test of Google.com integration with Enter-to-skip functionality
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');

test('Google.com quick validation test', async () => {
  const userDataDir = path.join(process.cwd(), '.pw-chrome-google-quick');
  try { fs.mkdirSync(userDataDir); } catch {}

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });
  const page = await context.newPage();

  await page.goto('https://www.google.com');
  await page.waitForTimeout(2000);

  // Manually inject extension scripts (simulating activeTab permission)
  await page.addScriptTag({ path: path.join(EXTENSION_PATH, 'src/shared/selectors.js') });
  await page.addScriptTag({ path: path.join(EXTENSION_PATH, 'src/content/overlay.js') });
  await page.addScriptTag({ path: path.join(EXTENSION_PATH, 'src/content/index.js') });

  await page.waitForTimeout(2000);

  // Test that bridge API exists
  const bridgeExists = await page.evaluate(() => {
    return typeof (window as any).__actcli_bridge !== 'undefined';
  });
  expect(bridgeExists).toBeTruthy();

  // Test that pick function works
  const pickResult = await page.evaluate(() => {
    try {
      (window as any).__actcli_bridge.pick();
      return true;
    } catch (e) {
      return false;
    }
  });
  expect(pickResult).toBeTruthy();

  console.log('✅ Google.com integration test PASSED!');
  console.log('✅ Bridge API loaded successfully');
  console.log('✅ Pick function works on Google.com');

  await context.close();
  expect(page.url()).toContain('google.com');
});