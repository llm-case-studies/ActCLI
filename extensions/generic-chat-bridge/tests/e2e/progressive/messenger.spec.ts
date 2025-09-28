import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { waitForBridge, injectProfile, validate, assertLastHistoryContains, launchExtensionContext, pgUrl } from './utils';

const mappingsDir = path.resolve(__dirname, '../mappings');

function loadMapping(name: string) {
  const p = path.join(mappingsDir, `${name}.json`);
  return JSON.parse(fs.readFileSync(p, 'utf8')) as { input: string; send?: string; history: string };
}

test.describe('Progressive • Messenger-like (WA/TG/RC)', () => {
  test('WA-like • inject → validate', async () => {
    const { page, close } = await launchExtensionContext('messenger-wa');
    await page.goto(pgUrl('wa.html'));
    await waitForBridge(page, 'messenger-wa');
    await injectProfile(page, loadMapping('wa'));
    const res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E');
    await close();
  });

  test('TG-like • inject → validate', async () => {
    const { page, close } = await launchExtensionContext('messenger-tg');
    await page.goto(pgUrl('tg.html'));
    await waitForBridge(page, 'messenger-tg');
    await injectProfile(page, loadMapping('tg'));
    const res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E');
    await close();
  });

  test('RC-like • inject → validate (+mutation)', async () => {
    const { page, close } = await launchExtensionContext('messenger-rc');
    await page.goto(pgUrl('rc.html'));
    await waitForBridge(page, 'messenger-rc');
    await injectProfile(page, loadMapping('rc'));
    let res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E');

    await page.check('#mutate');
    await waitForBridge(page, 'messenger-rc-after-mutate');
    res = await validate(page, 'E2E2');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E2');
    await close();
  });
});
