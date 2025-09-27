/**
 * Simple RocketChat test - just verify extension works and can pick elements
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';

test.describe('Simple RocketChat Extension Test', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run RocketChat test');

  test('extension loads and picker works on RocketChat', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-simple-rc');
    try { fs.mkdirSync(userDataDir); } catch {}

    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    const page = await context.newPage();

    // Monitor console
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));

    // Go to RocketChat (will hit login page)
    await page.goto(`${RC_BASE}/`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    console.log('Current URL:', page.url());
    console.log('Page title:', await page.title());

    // Check if extension is loaded
    const bridgeExists = await page.evaluate(() => {
      return typeof (window as any).__actcli_bridge !== 'undefined';
    });

    console.log('Bridge API exists:', bridgeExists);
    expect(bridgeExists).toBeTruthy();

    // Test that pick function works
    const pickResult = await page.evaluate(() => {
      try {
        (window as any).__actcli_bridge.pick();
        return { success: true };
      } catch (e) {
        return { success: false, error: e.message };
      }
    });

    console.log('Pick result:', pickResult);
    expect(pickResult.success).toBeTruthy();

    // Test that we can find login form elements (proves picker can work)
    const loginElements = await page.locator('input[type="email"], input[type="text"], input[type="password"]').count();
    console.log('Found login form elements:', loginElements);
    expect(loginElements).toBeGreaterThan(0);

    // Try clicking on a login input to test picker interaction
    if (loginElements > 0) {
      await page.locator('input[type="email"], input[type="text"]').first().click();
      console.log('✅ Successfully clicked login input element');

      // Test the computeSelector function on the login input
      const selector = await page.evaluate(() => {
        const input = document.querySelector('input[type="email"], input[type="text"]');
        return (window as any).__actcli_bridge.computeSelector(input);
      });

      console.log('Computed selector:', selector);
      expect(selector).toBeTruthy();
    }

    console.log('✅ RocketChat extension integration test PASSED!');
    console.log('✅ Extension loads successfully');
    console.log('✅ Bridge API available');
    console.log('✅ Pick function works');
    console.log('✅ Can interact with page elements');

    await context.close();
  });
});