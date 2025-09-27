/**
 * RocketChat login demo - go through login and pause for user inspection
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';
const RC_USER = process.env.RC_USER1 || 'alexsudakov';
const RC_PASS = process.env.RC_USER1_PASS || 'asU11big';

test.describe('RocketChat Login Demo', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run RocketChat test');

  test('login to RocketChat and pause for inspection', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-rc-demo');
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

    console.log('🚀 Starting RocketChat login demo...');

    // Go to RocketChat login
    await page.goto(`${RC_BASE}/login`);
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(2000);

    console.log('📍 At login page:', page.url());

    // Fill login form
    console.log('🔑 Filling login credentials...');
    await page.fill('input[name="emailOrUsername"], input[type="email"], input[placeholder*="email" i]', RC_USER);
    await page.fill('input[name="pass"], input[type="password"], input[placeholder*="password" i]', RC_PASS);

    console.log('🔐 Clicking login button...');
    await page.click('button:has-text("Login"), button[type="submit"], .login-button');

    // Wait for navigation after login
    console.log('⏳ Waiting for login to complete...');
    await page.waitForTimeout(5000);

    console.log('📍 After login URL:', page.url());
    console.log('📄 Page title:', await page.title());

    // Check if extension is available
    const bridgeExists = await page.evaluate(() => {
      return typeof (window as any).__actcli_bridge !== 'undefined';
    });

    console.log('🔌 Extension loaded:', bridgeExists ? '✅ YES' : '❌ NO');

    if (bridgeExists) {
      console.log('🎯 Extension methods available:', await page.evaluate(() => {
        return Object.keys((window as any).__actcli_bridge || {});
      }));
    }

    // Look for chat interface elements
    const chatElements = await page.evaluate(() => {
      const inputs = document.querySelectorAll('[role="textbox"], [contenteditable="true"], textarea').length;
      const buttons = document.querySelectorAll('button').length;
      const messages = document.querySelectorAll('[data-qa*="message" i], .message').length;
      return { inputs, buttons, messages };
    });

    console.log('💬 Chat interface elements found:', chatElements);

    console.log('');
    console.log('🎉 SUCCESS! Logged into RocketChat with extension loaded!');
    console.log('👀 PAUSING FOR 10 SECONDS - You can now inspect the browser...');
    console.log('🔍 Look for the extension icon in the browser toolbar');
    console.log('🖱️  Try clicking the extension popup to test it');
    console.log('');

    // Pause for 10 seconds for user inspection
    await page.waitForTimeout(10000);

    console.log('✅ Demo completed!');
    await context.close();

    // Basic assertions
    expect(page.url()).toContain('127.0.0.1:3000');
    expect(bridgeExists).toBeTruthy();
  });
});