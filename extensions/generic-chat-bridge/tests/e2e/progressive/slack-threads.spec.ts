import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { waitForBridge, injectProfile, validate, launchExtensionContext, pgUrl } from './utils';

const mappingsDir = path.resolve(__dirname, '../mappings');

function loadMapping(name: string) {
  const p = path.join(mappingsDir, `${name}.json`);
  return JSON.parse(fs.readFileSync(p, 'utf8')) as { input: string; send?: string; history: string };
}

test.describe('Progressive • Slack-like (threads)', () => {
  test('slack.html • main + thread mappings', async () => {
    const { page, close } = await launchExtensionContext('slack-threads');
    await page.goto(pgUrl('slack.html'));

    await waitForBridge(page, 'slack-main');
    await injectProfile(page, loadMapping('slack-main'));
    let res = await validate(page, 'E2E');
    expect(res?.ok).toBeTruthy();
    await page.locator('#history').locator('xpath=./*[last()]').waitFor();
    await page.locator('#history').locator('xpath=./*[last()]').isVisible();

    const reply = page.locator('[data-action="reply"]').first();
    if (await reply.count()) {
      await reply.click();
    } else {
      await page.check('#toggleThread');
    }

    const threadHistorySel = '#thread-history';
    await waitForBridge(page, 'slack-thread');
    await injectProfile(page, loadMapping('slack-thread'));
    res = await validate(page, 'E2E-THREAD');
    expect(res?.ok).toBeTruthy();
    await page.locator(threadHistorySel).locator('xpath=./*[last()]').waitFor();
    await page.locator(threadHistorySel).locator('xpath=./*[last()]').isVisible();
    await close();
  });
});
