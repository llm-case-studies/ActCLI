/**
 * Test extension on real Google.com with the new "Enter to skip Send" improvements
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');

test('Google.com real test with Enter-to-skip Send flow', async () => {
  const userDataDir = path.join(process.cwd(), '.pw-chrome-google-test');
  try { fs.mkdirSync(userDataDir); } catch {}

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });
  const page = await context.newPage();

  // Monitor console messages
  page.on('console', msg => {
    console.log(`PAGE [${msg.type()}]:`, msg.text());
  });

  // Go to Google.com
  await page.goto('https://www.google.com');
  await page.waitForTimeout(3000);

  console.log('Current URL:', page.url());
  console.log('Page title:', await page.title());

  // Check if our debug API is available
  const bridgeExists = await page.evaluate(() => {
    return typeof (window as any).__actcli_bridge !== 'undefined';
  });

  console.log('Bridge API exists:', bridgeExists);
  expect(bridgeExists).toBeTruthy();

  if (bridgeExists) {
    console.log('✅ Extension loaded on Google.com!');

    // Start the pick flow
    await page.evaluate(() => (window as any).__actcli_bridge.pick());
    console.log('✅ Pick mode started');

    // Wait a bit for the overlay to appear
    await page.waitForTimeout(2000);

    // Try to pick the search input (should be the main Google search box)
    const searchBox = page.locator('input[name="q"]').first();
    await searchBox.click();
    console.log('✅ Clicked search input');

    await page.waitForTimeout(1000);

    // Press Enter to skip the Send step (testing the new functionality)
    await page.keyboard.press('Enter');
    console.log('✅ Pressed Enter to skip Send step');

    await page.waitForTimeout(1000);

    // Now click on the results area (where search results would appear)
    // We'll click on the main content area
    const resultsArea = page.locator('#search, #center_col, #main').first();
    await resultsArea.click();
    console.log('✅ Clicked results area');

    await page.waitForTimeout(1000);

    // Try to validate the mapping
    const validationResult = await page.evaluate(async () => {
      return (window as any).__actcli_bridge.validate('Test Google search flow');
    });

    console.log('Validation result:', validationResult);

    // The validation should work with the new Enter-to-skip functionality
    expect(validationResult?.ok).toBeTruthy();

    console.log('✅ Google.com integration test passed!');
  }

  // Keep browser open for inspection
  await page.waitForTimeout(5000);
  await context.close();

  expect(page.url()).toContain('google.com');
});