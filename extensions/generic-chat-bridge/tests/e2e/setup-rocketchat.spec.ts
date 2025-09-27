/**
 * Rocket.Chat Setup Helper - Handle initial wizard if needed
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';

test.describe('Rocket.Chat Setup', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run setup test');

  test('complete setup wizard if needed', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-setup-rc');
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

    // Go to root
    await page.goto(RC_BASE);
    await page.waitForTimeout(3000);

    console.log('Initial URL:', page.url());
    console.log('Page title:', await page.title());

    // Look for setup/wizard elements
    const setupElements = await page.locator('text=/setup|wizard|admin.*setup|get.*started|welcome.*rocket/i').count();
    const loginElements = await page.locator('input[type="email"], input[type="password"]').count();
    const setupButtons = await page.getByRole('button', { name: /setup|start|continue|next/i }).count();

    console.log('Setup elements:', setupElements);
    console.log('Login elements:', loginElements);
    console.log('Setup buttons:', setupButtons);

    // Get all visible text to understand the page
    const pageText = await page.locator('body').textContent();
    const relevantText = pageText?.toLowerCase().substring(0, 500);
    console.log('Page content sample:', relevantText);

    // Try to find forms or input fields
    const allInputs = await page.locator('input').count();
    const allButtons = await page.locator('button').count();
    console.log('Total inputs:', allInputs);
    console.log('Total buttons:', allButtons);

    if (allButtons > 0) {
      const buttonTexts = await page.locator('button').allTextContents();
      console.log('Button texts:', buttonTexts.slice(0, 10));
    }

    // If there are setup elements, try to proceed through wizard
    if (setupElements > 0 || setupButtons > 0) {
      console.log('Found setup wizard, attempting to complete...');

      // Look for "Continue" or "Next" or "Setup" buttons
      const continueBtn = page.getByRole('button', { name: /continue|next|setup|start/i }).first();
      if (await continueBtn.count() > 0) {
        console.log('Clicking continue button...');
        await continueBtn.click();
        await page.waitForTimeout(2000);
        console.log('After continue URL:', page.url());
      }

      // Look for admin account creation form
      const nameField = page.locator('input[name="name"], input[placeholder*="name" i]').first();
      const emailField = page.locator('input[name="email"], input[type="email"]').first();
      const passwordField = page.locator('input[name="password"], input[type="password"]').first();

      if (await nameField.count() > 0 && await emailField.count() > 0) {
        console.log('Found admin creation form, filling...');
        await nameField.fill('Alex Sudakov');
        await emailField.fill('alexsudakov@prodigy.net');
        await passwordField.fill('asU11big');

        // Look for submit button
        const submitBtn = page.locator('button[type="submit"]').or(page.getByRole('button', { name: /create|save|finish|complete/i })).first();
        if (await submitBtn.count() > 0) {
          console.log('Submitting admin creation...');
          await submitBtn.click();
          await page.waitForTimeout(3000);
          console.log('After admin creation URL:', page.url());
        }
      }
    }

    // Keep browser open for manual inspection
    console.log('Setup attempt complete. Check browser for current state.');
    await page.waitForTimeout(10000);

    await context.close();
  });
});