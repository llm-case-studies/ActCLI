/**
 * Debug RocketChat login to see what's actually on the page
 */

import { test, expect, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

const RUN_OSS = process.env.RUN_OSS === '1' || process.env.RUN_OSS === 'true';
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../');
const RC_BASE = process.env.RC_BASE || 'http://127.0.0.1:3000';

test.describe('Debug RocketChat Login', () => {
  test.skip(!RUN_OSS, 'Set RUN_OSS=1 to run RocketChat test');

  test('debug login and see page content', async () => {
    const userDataDir = path.join(process.cwd(), '.pw-chrome-rc-debug');
    try { fs.mkdirSync(userDataDir); } catch {}

    const context = await chromium.launchPersistentContext(userDataDir, {
      headless: false,
      args: [
        `--disable-extensions-except=${EXTENSION_PATH}`,
        `--load-extension=${EXTENSION_PATH}`,
      ],
    });
    const page = await context.newPage();

    console.log('🚀 Starting RocketChat login debug...');

    // Login page
    await page.goto(`${RC_BASE}/login`);
    console.log('📍 At login page:', page.url());

    // Use the improved selectors
    const userField = page.getByLabel(/email|username/i).or(page.getByPlaceholder(/example@|username/i)).or(page.locator('input[name="emailOrUsername"], input[type="email"]'));

    try {
      await expect(userField.first()).toBeVisible({ timeout: 15000 });
      await userField.first().fill('alice');
      console.log('✅ Filled username: alice');
    } catch (e) {
      console.log('❌ Could not find username field:', e.message);

      // Debug: what inputs are available?
      const allInputs = await page.locator('input').all();
      console.log('📋 Available inputs:', await Promise.all(allInputs.map(async (input) => {
        const type = await input.getAttribute('type') || 'text';
        const name = await input.getAttribute('name') || '';
        const placeholder = await input.getAttribute('placeholder') || '';
        return { type, name, placeholder };
      })));
    }

    const passField = page.getByLabel(/password/i).or(page.locator('input[name="pass"], input[type="password"]'));

    try {
      await expect(passField.first()).toBeVisible({ timeout: 15000 });
      await passField.first().fill('alicepass');
      console.log('✅ Filled password');
    } catch (e) {
      console.log('❌ Could not find password field:', e.message);
    }

    // Click login
    const loginBtn = page.getByRole('button', { name: /login|sign in/i }).first();
    if (await loginBtn.count()) {
      await loginBtn.click();
      console.log('✅ Clicked login button');
    } else {
      await page.click('button[type="submit"], button:has-text("Login"), button:has-text("Sign In")');
      console.log('✅ Clicked login button (fallback)');
    }

    // Wait for navigation
    await page.waitForLoadState('domcontentloaded');
    await page.waitForTimeout(3000);

    console.log('📍 After login URL:', page.url());
    console.log('📄 Page title:', await page.title());

    // Try to navigate to the e2e channel
    await page.goto(`${RC_BASE}/channel/e2e`);
    await page.waitForTimeout(3000);

    console.log('📍 Channel URL:', page.url());

    // Check what's actually on the page
    const pageContent = await page.evaluate(() => {
      const textBoxes = document.querySelectorAll('[role="textbox"]').length;
      const contentEditables = document.querySelectorAll('[contenteditable="true"]').length;
      const textareas = document.querySelectorAll('textarea').length;
      const inputs = document.querySelectorAll('input').length;
      const buttons = document.querySelectorAll('button').length;

      return {
        textBoxes,
        contentEditables,
        textareas,
        inputs,
        buttons,
        url: window.location.href,
        title: document.title
      };
    });

    console.log('📊 Page content analysis:', pageContent);

    // Check if extension loaded
    const bridgeExists = await page.evaluate(() => {
      return typeof (window as any).__actcli_bridge !== 'undefined';
    });
    console.log('🔌 Extension bridge exists:', bridgeExists);

    // Look for specific RocketChat elements
    const rcElements = await page.evaluate(() => {
      const messageInput = document.querySelector('[data-qa="message-box"], .message-form input, .rc-input');
      const sendButton = document.querySelector('[data-qa="send-message"], .send-button');
      const messagesList = document.querySelector('[data-qa="messages"], .messages-box, .message-list');

      return {
        messageInput: messageInput ? messageInput.tagName + '.' + messageInput.className : 'not found',
        sendButton: sendButton ? sendButton.tagName + '.' + sendButton.className : 'not found',
        messagesList: messagesList ? messagesList.tagName + '.' + messagesList.className : 'not found'
      };
    });

    console.log('🎯 RocketChat specific elements:', rcElements);

    // Pause for inspection
    console.log('⏸️  Pausing for 10 seconds for manual inspection...');
    await page.waitForTimeout(10000);

    await context.close();
  });
});