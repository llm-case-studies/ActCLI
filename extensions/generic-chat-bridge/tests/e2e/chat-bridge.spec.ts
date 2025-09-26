import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const BASE_URL = process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400';

test.describe('BrExt • Playground E2E (Learn→Validate→Re-learn)', () => {
  test('textarea.html end-to-end using debug API', async () => {
    // Persistent context is required for extensions
    const userDataDir = path.join(process.cwd(), '.pw-chrome-profile');
    try { fs.mkdirSync(userDataDir); } catch {}
    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    const page = await context.newPage();

    // Listen for console messages and errors
    page.on('console', msg => console.log('PAGE LOG:', msg.text()));
    page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

    await page.goto(`${BASE_URL}/textarea.html`);
    // Wait for content scripts to load and API to be ready
    await page.waitForFunction(() => Boolean((window as any).__actcli_bridge && (window as any).__actcli_bridge.pick), { timeout: 10000 });
    // Start picking via exposed debug API
    await page.evaluate(() => (window as any).__actcli_bridge.pick());
    await page.click('#composer');
    await page.click('#send');
    await page.click('#history');

    // Validate via debug API
    const res = await page.evaluate(async () => {
      const r = await (window as any).__actcli_bridge.validate('E2E-Message');
      return r;
    });
    expect(res?.ok).toBeTruthy();

    // Check a message appeared
    await expect(page.locator('#history .msg').last()).toHaveText(/E2E-Message/);

    await context.close();
  });

  test('contenteditable.html validate', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-profile2');
    try { fs.mkdirSync(userDataDir); } catch {}
    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    const page = await context.newPage();
    await page.goto(`${BASE_URL}/contenteditable.html`);
    await page.waitForFunction(() => Boolean((window as any).__actcli_bridge && (window as any).__actcli_bridge.pick));
    await page.evaluate(() => (window as any).__actcli_bridge.pick());
    await page.click('[role="textbox"]');
    await page.click('#send');
    await page.click('#history');
    const res = await page.evaluate(async () => (window as any).__actcli_bridge.validate('CE-E2E'));
    expect(res?.ok).toBeTruthy();
    await expect(page.locator('#history .msg').last()).toHaveText(/CE-E2E/);
    await context.close();
  });
});
