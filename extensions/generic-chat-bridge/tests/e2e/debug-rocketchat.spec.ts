/**
 * Debug Rocket.Chat Extension Loading
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';

test.describe('Debug Rocket.Chat Extension', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run');

  test('debug extension on rocket.chat', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-debug-rc');
    try { fs.mkdirSync(userDataDir); } catch {}

    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    const page = await context.newPage();

    // Monitor all console messages
    page.on('console', msg => {
      console.log(`PAGE [${msg.type()}]:`, msg.text());
    });

    page.on('pageerror', error => {
      console.log('PAGE ERROR:', error.message);
    });

    // Go to Rocket.Chat
    await page.goto(RC_BASE);
    await page.waitForTimeout(3000);

    console.log('Current URL:', page.url());
    console.log('Page title:', await page.title());

    // Check if our debug API is available
    const bridgeExists = await page.evaluate(() => {
      return typeof (window as any).__actcli_bridge !== 'undefined';
    });

    console.log('Bridge API exists:', bridgeExists);

    if (bridgeExists) {
      console.log('✅ SUCCESS: Extension working on Rocket.Chat!');

      const bridgeMethods = await page.evaluate(() => {
        const bridge = (window as any).__actcli_bridge;
        return bridge ? Object.keys(bridge) : [];
      });
      console.log('Bridge methods:', bridgeMethods);

    } else {
      console.log('❌ Extension not loaded on Rocket.Chat');

      // Check what scripts are loaded
      const scriptsInfo = await page.evaluate(() => {
        return {
          hasSelectors: typeof (window as any).computeSelector !== 'undefined',
          hasOverlay: typeof (window as any)._overlay !== 'undefined',
          documentReady: document.readyState,
          url: window.location.href
        };
      });
      console.log('Scripts info:', scriptsInfo);
    }

    // Keep open for inspection
    await page.waitForTimeout(5000);
    await context.close();

    console.log('Test completed - extension availability:', bridgeExists);
  });
});