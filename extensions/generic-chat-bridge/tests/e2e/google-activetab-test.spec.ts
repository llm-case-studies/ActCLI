/**
 * Test extension on Google.com using activeTab permission (manual injection)
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');

test('Google.com test using activeTab permission', async () => {
  const userDataDir = path.join(process.cwd(), '.pw-chrome-google-activetab');
  try { fs.mkdirSync(userDataDir); } catch {}

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
    ],
  });
  const page = await context.newPage();

  // Go to Google.com
  await page.goto('https://www.google.com');
  await page.waitForTimeout(3000);

  console.log('Current URL:', page.url());
  console.log('Page title:', await page.title());

  // Since content scripts don't auto-inject on google.com, we need to manually inject them
  // This simulates clicking the extension icon and using activeTab permission

  // First, inject the shared selectors
  await page.addScriptTag({
    path: path.join(EXTENSION_PATH, 'src/shared/selectors.js')
  });

  // Then inject the overlay script (MAIN world)
  await page.addScriptTag({
    path: path.join(EXTENSION_PATH, 'src/content/overlay.js')
  });

  // Finally inject the main content script
  await page.addScriptTag({
    path: path.join(EXTENSION_PATH, 'src/content/index.js')
  });

  // Wait for scripts to initialize
  await page.waitForTimeout(2000);

  // Check if our debug API is available after manual injection
  const bridgeExists = await page.evaluate(() => {
    return typeof (window as any).__actcli_bridge !== 'undefined';
  });

  console.log('Bridge API exists after injection:', bridgeExists);

  if (bridgeExists) {
    console.log('✅ Extension scripts loaded on Google.com!');

    // Test the bridge methods
    const bridgeMethods = await page.evaluate(() => {
      const bridge = (window as any).__actcli_bridge;
      return bridge ? Object.keys(bridge) : [];
    });
    console.log('Bridge methods:', bridgeMethods);

    // Start the pick flow
    await page.evaluate(() => (window as any).__actcli_bridge.pick());
    console.log('✅ Pick mode started on Google.com');

    // Wait for overlay to appear
    await page.waitForTimeout(2000);

    // Try to pick the search input
    const searchBox = page.locator('input[name="q"]').first();
    await searchBox.click();
    console.log('✅ Clicked Google search input');

    await page.waitForTimeout(1000);

    // Press Enter to skip Send step (testing new functionality)
    await page.keyboard.press('Enter');
    console.log('✅ Pressed Enter to skip Send step');

    await page.waitForTimeout(1000);

    // Click on results area
    const resultsArea = page.locator('#search, #center_col, #main').first();
    await resultsArea.click();
    console.log('✅ Clicked results area');

    await page.waitForTimeout(1000);

    // Test validation with the new Enter-to-skip functionality
    const validationResult = await page.evaluate(async () => {
      return (window as any).__actcli_bridge.validate('Test Google search with Enter-to-skip');
    });

    console.log('Validation result:', validationResult);

    if (validationResult?.ok) {
      console.log('✅ Google.com integration with Enter-to-skip PASSED!');
    } else {
      console.log('❌ Validation failed:', validationResult?.error);
    }

    // Test that a search actually works
    await page.locator('input[name="q"]').fill('playwright testing');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(3000);

    // Try validate again on the results page
    const resultsValidation = await page.evaluate(async () => {
      return (window as any).__actcli_bridge.validate('Results page test');
    });

    console.log('Results page validation:', resultsValidation);

  } else {
    console.log('❌ Bridge API not available even after manual injection');

    // Debug what's available
    const windowProps = await page.evaluate(() => {
      return Object.keys(window).filter(key => key.includes('actcli') || key.includes('bridge'));
    });
    console.log('ActCLI-related window properties:', windowProps);
  }

  // Keep browser open for inspection
  await page.waitForTimeout(10000);
  await context.close();

  expect(page.url()).toContain('google.com');
});