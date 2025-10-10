import { test, expect } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { waitForBridge, injectProfile, validate, assertLastHistoryContains, launchExtensionContext, pgUrl } from './utils';

const mappingsDir = path.resolve(__dirname, '../mappings');

function load(name: string) {
  return JSON.parse(fs.readFileSync(path.join(mappingsDir, `${name}.json`), 'utf8')) as { input: string; send?: string; history: string };
}

test.describe('Progressive • Relay (Seminar ↔ Remote)', () => {
  test('relay.html • map Seminar (left), send from Remote (right) → Seminar sees message; then Seminar → Remote', async () => {
    const { page, close } = await launchExtensionContext('relay');
    await page.goto(pgUrl('relay.html'));
    await waitForBridge(page, 'relay');
    // Map seminar (left) panel
    await injectProfile(page, load('relay'));
    // Remote sends a message (right input); we simulate typing and Enter
    await page.click('[data-qa="relay-right-input"]');
    await page.keyboard.type('REMOTE-E2E');
    await page.keyboard.press('Enter');
    // Verify Seminar (left) history mirrors the message
    await assertLastHistoryContains(page, '#sem-history', 'REMOTE-E2E');
    // Now send from Seminar via extension validate and assert Remote mirrors
    const res = await validate(page, 'SEMINAR-E2E');
    expect(res?.ok).toBeTruthy();
    await assertLastHistoryContains(page, '#rem-history', 'SEMINAR-E2E');
    await close();
  });
});

