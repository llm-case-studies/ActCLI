/**
 * Debug Extension Loading - Test on google.com to verify basic functionality
 */

import { test, expect, chromium } from '@playwright/test';
import { playgroundUrl } from './urls';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');

test.describe('Debug Extension Loading', () => {
  test('test extension loads on google.com', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-debug-ext');
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

    // Monitor page errors
    page.on('pageerror', error => {
      console.log('PAGE ERROR:', error.message);
    });

    // Go to playground which should match our patterns
    await page.goto(playgroundUrl('textarea.html'));
    await page.waitForTimeout(3000);

    console.log('Current URL:', page.url());
    console.log('Page title:', await page.title());

    // Check if our debug API is available
    const bridgeExists = await page.evaluate(() => {
      return typeof (window as any).__actcli_bridge !== 'undefined';
    });

    console.log('Bridge API exists:', bridgeExists);

    if (bridgeExists) {
      console.log('✅ SUCCESS: Extension loaded and bridge API available!');

      // Try to get bridge methods
      const bridgeMethods = await page.evaluate(() => {
        const bridge = (window as any).__actcli_bridge;
        return bridge ? Object.keys(bridge) : [];
      });
      console.log('Bridge methods:', bridgeMethods);

      // Try the pick function
      try {
        await page.evaluate(() => (window as any).__actcli_bridge.pick());
        console.log('✅ Pick function called successfully');
      } catch (e) {
        console.log('❌ Pick function failed:', e.message);
      }

    } else {
      console.log('❌ Bridge API not found - checking why...');

      // Check if content scripts are running at all
      const scriptsInfo = await page.evaluate(() => {
        // Look for any signs our scripts loaded
        return {
          hasSelectors: typeof (window as any).computeSelector !== 'undefined',
          hasOverlay: typeof (window as any)._overlay !== 'undefined',
          documentReady: document.readyState
        };
      });
      console.log('Scripts info:', scriptsInfo);
    }

    // Check for service worker in extension
    const extensions = await context.backgroundPages();
    console.log('Background pages:', extensions.length);

    if (extensions.length > 0) {
      const bgPage = extensions[0];
      console.log('Background page URL:', bgPage.url());

      // Listen to background page console
      bgPage.on('console', msg => {
        console.log(`BG [${msg.type()}]:`, msg.text());
      });
    }

    // Keep browser open for inspection
    await page.waitForTimeout(10000);
    await context.close();

    // Basic assertion
    expect(page.url()).toContain('google.com');
  });
});
