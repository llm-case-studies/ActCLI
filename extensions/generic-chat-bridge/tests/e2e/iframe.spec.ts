/**
 * BrExt • Same-origin Iframe E2E
 *
 * Goals
 * - Demonstrate interacting with content scripts injected into frames (`all_frames: true`)
 * - Show how to access MAIN-world debug API within a frame context
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const BASE_URL = process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400';

test('iframe.html • pick → validate inside same-origin iframe', async () => {
  const userDataDir = path.join(process.cwd(), '.pw-chrome-iframe');
  try { fs.mkdirSync(userDataDir); } catch {}
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });
  const page = await context.newPage();
  await page.goto(`${BASE_URL}/iframe.html`);

  // Access the child frame (same-origin)
  const frameLocator = page.frameLocator('iframe');

  // Wait for the iframe to load, then wait for the MAIN-world debug API to be ready
  await frameLocator.locator('body').waitFor();

  // Get the actual frame to access its page context
  const frames = page.frames();
  const iframe = frames.find(f => f.url().includes('textarea.html'));
  if (!iframe) throw new Error('iframe not found');

  await iframe.waitForFunction(() => Boolean((window as any).__actcli_bridge?.pick));

  // Trigger picking and selection within the frame
  await iframe.evaluate(() => (window as any).__actcli_bridge.pick());
  await frameLocator.locator('#composer').click();
  await page.waitForTimeout(100); // Small delay between picks
  await frameLocator.locator('#send').click();
  await page.waitForTimeout(100); // Small delay between picks
  await frameLocator.locator('#history').click();
  await page.waitForTimeout(300); // Wait for profile to save

  const res = await iframe.evaluate(async () => (window as any).__actcli_bridge.validate('IFR-E2E'));
  expect(res?.ok).toBeTruthy();
  await expect(frameLocator.locator('#history .msg').last()).toHaveText(/IFR-E2E/);

  await context.close();
});

