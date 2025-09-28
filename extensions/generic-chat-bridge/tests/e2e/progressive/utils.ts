import { expect, Page, Frame, chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';

export const BASE_URL = process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400';

export function playgroundBase() {
  const trimmed = BASE_URL.replace(/\/$/, '');
  if (/\/playground$/i.test(trimmed)) return trimmed;
  return `${trimmed}/playground`;
}

export function pgUrl(page: string) {
  const base = playgroundBase();
  const rel = String(page).replace(/^\//, '');
  return `${base}/${rel}`;
}
const EXTENSION_PATH = process.env.EXTENSION_PATH || path.resolve(__dirname, '../../../');

export async function launchExtensionContext(name: string) {
  const userDataDir = path.join(process.cwd(), `.pw-chrome-progressive-${slug(name)}`);
  try { fs.mkdirSync(userDataDir); } catch {}
  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    viewport: { width: 1700, height: 1100 },
    args: [
      `--disable-extensions-except=${EXTENSION_PATH}`,
      `--load-extension=${EXTENSION_PATH}`,
      `--window-size=1700,1100`,
    ],
  });
  const page = await context.newPage();
  return { context, page, close: () => context.close() };
}

type Target = Page | Frame;

export async function waitForBridge(target: Target, name: string, timeoutMs = 10000) {
  try {
    await target.waitForFunction(() => Boolean((window as any).__actcli_bridge?.validate), { timeout: timeoutMs });
  } catch (err) {
    // Best-effort screenshot on failure (only if target supports it)
    const anyTarget: any = target as any;
    if (typeof anyTarget.screenshot === 'function') {
      try { await anyTarget.screenshot({ path: `progressive-${slug(name)}-bridge-missing.png`, fullPage: true }); } catch {}
    }
    throw new Error(`[${name}] __actcli_bridge not available within ${timeoutMs}ms`);
  }
}

export async function injectProfile(target: Target, profile: { input: string; history: string; send?: string }) {
  // Try the message API first; fall back to postMessage picks for determinism (no overlay clicks)
  await target.evaluate(async (p) => {
    const w: any = window as any;
    try {
      if (w.chrome?.runtime?.sendMessage) {
        await new Promise((resolve) => w.chrome.runtime.sendMessage({ type: 'content.injectProfile', profile: p }, () => resolve(true)));
        return true;
      }
    } catch {}
    // Fallback: simulate overlay pick messages directly
    w.postMessage({ __actcli_pick: true, stage: 'input', selector: p.input }, '*');
    w.postMessage({ __actcli_pick: true, stage: 'send', selector: p.send || '__ENTER__' }, '*');
    w.postMessage({ __actcli_pick: true, stage: 'history', selector: p.history }, '*');
    return true;
  }, profile);
  // Allow content script to persist the profile
  await target.waitForTimeout(200);
}

export async function validate(target: Target, text: string) {
  return await target.evaluate(async (t) => (window as any).__actcli_bridge.validate(t), text);
}

export async function assertLastHistoryContains(target: Target, historySelector: string, text: string, scrollContainerSelector?: string) {
  // If provided, actively scroll virtualization viewport and look for ANY message containing the text
  if (scrollContainerSelector) {
    for (let i = 0; i < 12; i++) {
      await target.evaluate((sel) => {
        const vp = document.querySelector(sel as string) as HTMLElement | null;
        if (vp) vp.scrollTop = vp.scrollHeight;
      }, scrollContainerSelector);
      const match = target.locator(`${historySelector} .msg`, { hasText: text });
      if (await match.count()) return;
      await target.waitForTimeout(200);
    }
  }
  // Try a non-virtualized path: any .msg contains text
  const anyMatch = target.locator(`${historySelector} .msg`, { hasText: text });
  if (await anyMatch.count()) return;
  // Final fallback: container contains the text
  await expect(target.locator(historySelector)).toContainText(text);
}

function slug(s: string) {
  return String(s).toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
}
