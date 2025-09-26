// ActCLI Web Chat Bridge — Background (Service Worker)
// Purpose: orchestrate storage, tab messaging, and (later) Semhost MCP calls.
// Minimal, ToS-safe: no provider-specific logic; no automation beyond user‑initiated flows.

const STORAGE_KEY = 'actcli_web_bridge_profiles_v1';

// Utility: get tab origin key (hostname only to scope profiles per-origin)
function originKeyFromUrl(url) {
  try {
    const u = new URL(url);
    return u.origin;
  } catch {
    return null;
  }
}

async function loadProfiles() {
  const data = await chrome.storage.local.get(STORAGE_KEY);
  return data[STORAGE_KEY] || {};
}

async function saveProfiles(map) {
  await chrome.storage.local.set({ [STORAGE_KEY]: map });
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

// Message router (popup/content → background)
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg?.type === 'bridge.saveProfile') {
      const { origin, profile } = msg;
      const map = await loadProfiles();
      map[origin] = profile;
      await saveProfiles(map);
      sendResponse({ ok: true });
      return;
    }
    if (msg?.type === 'bridge.getProfile') {
      const { origin } = msg;
      const map = await loadProfiles();
      sendResponse({ ok: true, profile: map[origin] || null });
      return;
    }
    if (msg?.type === 'bridge.deleteProfile') {
      const { origin } = msg;
      const map = await loadProfiles();
      delete map[origin];
      await saveProfiles(map);
      sendResponse({ ok: true });
      return;
    }
    if (msg?.type === 'bridge.pickStart') {
      const tab = await getActiveTab();
      if (!tab?.id) { sendResponse({ ok: false, error: 'no-active-tab' }); return; }
      await chrome.tabs.sendMessage(tab.id, { type: 'content.picker.start' });
      sendResponse({ ok: true });
      return;
    }
    if (msg?.type === 'bridge.validate') {
      const tab = await getActiveTab();
      if (!tab?.id) { sendResponse({ ok: false, error: 'no-active-tab' }); return; }
      const { text } = msg;
      await chrome.tabs.sendMessage(tab.id, { type: 'content.validate', text });
      sendResponse({ ok: true });
      return;
    }
    if (msg?.type === 'bridge.connect') {
      // Placeholder: in a later sprint, call Semhost /mcp/rpc to register participant
      // while we only persist local state to respect ToS and keep scope OSS-only.
      const tab = await getActiveTab();
      const ok = !!tab?.url;
      const origin = ok ? originKeyFromUrl(tab.url) : null;
      sendResponse({ ok, origin });
      return;
    }
  })();
  // Indicate async response
  return true;
});

