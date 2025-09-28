import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { waitForBridge, injectProfile, validate, assertLastHistoryContains, launchExtensionContext, pgUrl } from './utils';

const mappingsDir = path.resolve(__dirname, '../mappings');

function loadMapping(name: string) {
  const p = path.join(mappingsDir, `${name}.json`);
  return JSON.parse(fs.readFileSync(p, 'utf8')) as { input: string; send?: string; history: string };
}

test.describe('Progressive • Basic mocks', () => {
  test('textarea.html • inject → validate', async () => {
    const { page, close } = await launchExtensionContext('basic-textarea');
    await page.goto(pgUrl('textarea.html'));
    await waitForBridge(page, 'basic-textarea');
    await injectProfile(page, loadMapping('textarea'));
    const res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E');
    await close();
  });

  test('contenteditable.html • inject → validate', async () => {
    const { page, close } = await launchExtensionContext('basic-contenteditable');
    await page.goto(pgUrl('contenteditable.html'));
    await waitForBridge(page, 'basic-contenteditable');
    await injectProfile(page, loadMapping('contenteditable'));
    const res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E');
    await close();
  });

  test('minimal.html • inject → validate', async () => {
    const { page, close } = await launchExtensionContext('basic-minimal');
    await page.goto(pgUrl('minimal.html'));
    await waitForBridge(page, 'basic-minimal');
    await injectProfile(page, loadMapping('minimal'));
    const res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E');
    await close();
  });

  test('virtualized.html • inject → validate (scrolling)', async () => {
    const { page, close } = await launchExtensionContext('basic-virtualized');
    await page.goto(pgUrl('virtualized.html'));
    await waitForBridge(page, 'basic-virtualized');
    await injectProfile(page, loadMapping('virtualized'));
    const res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E', '#viewport');
    await close();
  });

  test('iframe.html • inject → validate (frame)', async () => {
    const { page, close } = await launchExtensionContext('basic-iframe');
    await page.goto(pgUrl('iframe.html'));
    const frameLocator = page.frameLocator('iframe');
    await frameLocator.locator('body').waitFor();
    let iframe = page.frames().find(f => /textarea\.html/.test(f.url()));
    for (let i = 0; i < 20 && !iframe; i++) {
      await page.waitForTimeout(200);
      iframe = page.frames().find(f => /textarea\.html/.test(f.url()));
    }
    if (!iframe) throw new Error('Child iframe not found');
    await waitForBridge(iframe, 'basic-iframe');
    const mapping = loadMapping('iframe');
    await injectProfile(iframe, mapping);
    const res = await validate(iframe, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(iframe, '#history', 'E2E');
    await close();
  });
});
