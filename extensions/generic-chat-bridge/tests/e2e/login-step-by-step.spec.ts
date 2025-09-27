/**
 * Step-by-step login debug to see exactly where it fails
 */

import { test, expect, chromium } from '@playwright/test';
import { loadDotEnv } from './env';
import path from 'path';
import fs from 'fs';

loadDotEnv();

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';
const RC_USER = process.env.RC_USER1 || process.env.RC_ADMIN_EMAIL || 'alice';
const RC_PASS = process.env.RC_USER1_PASS || process.env.RC_ADMIN_PASS || 'alicepass';

test.describe('Step by Step Login Debug', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run login debug');

  test('step by step login with full logging', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-step-debug');
    try { fs.mkdirSync(userDataDir); } catch {}

    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    const page = await context.newPage();

    // Log all network activity
    page.on('response', response => {
      console.log(`📡 ${response.status()} ${response.url()}`);
    });

    console.log('🚀 Step-by-step login debug starting...');
    console.log('🔑 Using credentials: username="' + RC_USER + '" password="' + RC_PASS + '"');

    // Step 1: Navigate to login
    console.log('\n📍 STEP 1: Navigate to /login');
    await page.goto(`${RC_BASE}/login`);
    console.log('Current URL:', page.url());
    console.log('Page title:', await page.title());

    // Step 2: Wait and check page state
    console.log('\n⏳ STEP 2: Wait for page to load');
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    // Step 3: Find and fill username
    console.log('\n👤 STEP 3: Find and fill username field');
    const userField = page.getByLabel(/email|username/i)
      .or(page.getByPlaceholder(/example@|username|email/i))
      .or(page.locator('input[name="emailOrUsername"], input[type="email"], input[name*="user"]'));

    const userFieldCount = await userField.count();
    console.log('Username field candidates found:', userFieldCount);

    if (userFieldCount > 0) {
      const isVisible = await userField.first().isVisible();
      console.log('First username field visible:', isVisible);

      if (isVisible) {
        await userField.first().fill(RC_USER);
        console.log('✅ Username filled successfully');

        // Verify it was filled
        const filledValue = await userField.first().inputValue();
        console.log('Username field value after fill:', `"${filledValue}"`);
      } else {
        console.log('❌ Username field not visible');
      }
    } else {
      console.log('❌ No username field found');
    }

    // Step 4: Find and fill password
    console.log('\n🔒 STEP 4: Find and fill password field');
    const passField = page.getByLabel(/password/i)
      .or(page.locator('input[name="pass"], input[type="password"]'));

    const passFieldCount = await passField.count();
    console.log('Password field candidates found:', passFieldCount);

    if (passFieldCount > 0) {
      const isVisible = await passField.first().isVisible();
      console.log('First password field visible:', isVisible);

      if (isVisible) {
        await passField.first().fill(RC_PASS);
        console.log('✅ Password filled successfully');

        // Verify it was filled (don't log actual password value)
        const filledValue = await passField.first().inputValue();
        console.log('Password field filled length:', filledValue.length);
      } else {
        console.log('❌ Password field not visible');
      }
    } else {
      console.log('❌ No password field found');
    }

    // Step 5: Find and click login button
    console.log('\n🔘 STEP 5: Find and click login button');
    const loginBtn = page.getByRole('button', { name: /login|sign in/i });
    const loginBtnCount = await loginBtn.count();
    console.log('Login button candidates found:', loginBtnCount);

    if (loginBtnCount > 0) {
      const isVisible = await loginBtn.first().isVisible();
      console.log('First login button visible:', isVisible);

      if (isVisible) {
        await loginBtn.first().click();
        console.log('✅ Login button clicked');
      } else {
        console.log('❌ Login button not visible, trying fallback selectors');
        await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');
        console.log('✅ Fallback login button clicked');
      }
    } else {
      console.log('❌ No login button found');
    }

    // Step 6: Wait and check result
    console.log('\n⏳ STEP 6: Wait for login result');
    await page.waitForLoadState('domcontentloaded', { timeout: 10000 });
    await page.waitForTimeout(3000);

    console.log('URL after login:', page.url());
    console.log('Title after login:', await page.title());

    // Step 7: Test channel navigation
    console.log('\n🏠 STEP 7: Try to navigate to channel');
    await page.goto(`${RC_BASE}/channel/e2e`);
    await page.waitForTimeout(2000);

    console.log('URL after channel navigation:', page.url());
    console.log('Title after channel navigation:', await page.title());

    // Check if redirected back to login
    if (page.url().includes('/login')) {
      console.log('❌ FAILED: Redirected back to login page');

      // Look for error messages
      const errors = await page.evaluate(() => {
        const errorElements = Array.from(document.querySelectorAll('[role="alert"], .error, .alert, [class*="error"], [class*="alert"]'));
        return errorElements.map(el => el.textContent?.trim()).filter(text => text);
      });

      if (errors.length > 0) {
        console.log('🚨 Error messages found:', errors);
      } else {
        console.log('🤷 No error messages found');
      }

      // Take screenshot
      await page.screenshot({ path: 'login-failed-debug.png', fullPage: true });
      console.log('📸 Screenshot saved as login-failed-debug.png');
    } else {
      console.log('✅ SUCCESS: Not redirected to login, seems to be logged in');
    }

    // Pause for manual inspection
    console.log('\n⏸️  Pausing for 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);

    await context.close();
  });
});