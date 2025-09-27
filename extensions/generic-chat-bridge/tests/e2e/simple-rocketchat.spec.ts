/**
 * Simple Rocket.Chat test - just try to login and see what happens
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';
const RC_USER = process.env.RC_USER1 || 'alexsudakov';
const RC_PASS = process.env.RC_USER1_PASS || 'asU11big';

test.describe('Simple Rocket.Chat Login', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run Rocket.Chat test');

  test('try login and see what happens', async () => {
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

    // Monitor console for errors
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));

    // Go to login page
    await page.goto(`${RC_BASE}/login`);
    await page.waitForTimeout(2000);

    console.log('Current URL:', page.url());
    console.log('Page title:', await page.title());

    // Try to find and fill login form
    const emailInput = page.locator('input[name="emailOrUsername"], input[type="email"], input[placeholder*="Username" i]');
    const passInput = page.locator('input[name="pass"], input[type="password"]');

    if (await emailInput.count() > 0) {
      console.log('Found email input, filling...');
      await emailInput.fill(RC_USER);
      await passInput.fill(RC_PASS);

      // Find and click login button
      const loginBtn = page.getByRole('button', { name: /login|sign in/i }).first();
      if (await loginBtn.count() > 0) {
        console.log('Found login button, clicking...');
        await loginBtn.click();

        // Wait for navigation
        await page.waitForTimeout(3000);
        console.log('After login URL:', page.url());

        // Check if we're logged in by looking for common post-login elements
        const loggedIn = await page.locator('[role="main"], .main-content, .sidebar').count() > 0;
        console.log('Appears logged in:', loggedIn);

        if (loggedIn) {
          // Wait for the debug API
          try {
            await page.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick), { timeout: 10000 });
            console.log('Extension debug API is available!');

            // Look for any text input that might be a message composer
            const inputCand = page.locator('[role="textbox"], [contenteditable="true"], textarea, input[type="text"]');
            const inputCount = await inputCand.count();
            console.log('Found potential input elements:', inputCount);

            if (inputCount > 0) {
              console.log('SUCCESS: Found input elements - extension integration working!');
            }
          } catch (e) {
            console.log('Extension API not ready:', e.message);
          }
        }
      } else {
        console.log('No login button found');
      }
    } else {
      console.log('No login form found - might be setup wizard or different page');
    }

    // Keep browser open briefly for inspection
    await page.waitForTimeout(5000);
    await context.close();
  });
});