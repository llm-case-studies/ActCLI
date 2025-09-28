import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { waitForBridge, injectProfile, validate, assertLastHistoryContains, launchExtensionContext, pgUrl } from './utils';

const mappingsDir = path.resolve(__dirname, '../mappings');

function loadMapping(name: string) {
  const p = path.join(mappingsDir, `${name}.json`);
  return JSON.parse(fs.readFileSync(p, 'utf8')) as { input: string; send?: string; history: string };
}

test.describe('Progressive • Preply-like (chat + board)', () => {
  test('preply.html • inject → validate + canvas draw', async () => {
    const { page, close } = await launchExtensionContext('preply');
    await page.goto(pgUrl('preply.html'));
    await waitForBridge(page, 'preply');
    await injectProfile(page, loadMapping('preply'));

    const res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#history', 'E2E');

    const canvas = page.locator('#canvas');
    await canvas.scrollIntoViewIfNeeded();
    const box = await canvas.boundingBox();
    if (box) {
      await page.mouse.move(box.x + box.width / 2 - 20, box.y + box.height / 2 - 10);
      await page.mouse.down();
      await page.mouse.move(box.x + box.width / 2 + 20, box.y + box.height / 2 + 10);
      await page.mouse.up();
    }
    await close();
  });
});
