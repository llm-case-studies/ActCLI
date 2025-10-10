// ActCLI Web Chat Bridge — Background (Service Worker)
// Purpose: orchestrate storage, tab messaging, and (later) Semhost MCP calls.
// Minimal, ToS-safe: no provider-specific logic; no automation beyond user‑initiated flows.

const STORAGE_KEY = 'actcli_web_bridge_profiles_v1';
const CONFIG_KEY = 'actcli_web_bridge_config_v1';
const STATE_KEY = 'actcli_web_bridge_state_v1'; // per-origin runtime state (participant, session, toggles, activity)

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

async function loadState() {
  const data = await chrome.storage.local.get(STATE_KEY);
  return data[STATE_KEY] || {};
}

async function saveState(map) {
  await chrome.storage.local.set({ [STATE_KEY]: map });
}

async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function loadConfig() {
  const data = await chrome.storage.local.get(CONFIG_KEY);
  const cfg = data[CONFIG_KEY] || {};
  return { semhostUrl: cfg.semhostUrl || 'http://127.0.0.1:7530' };
}

async function saveConfig(cfg) {
  const current = await loadConfig();
  const merged = { ...current, ...cfg };
  await chrome.storage.local.set({ [CONFIG_KEY]: merged });
  return merged;
}

async function mcpCall(tool, params) {
  const { semhostUrl } = await loadConfig();
  const url = (semhostUrl || '').replace(/\/$/, '');
  const rpcRes = await fetch(`${url}/mcp/rpc`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ tool, params }),
  });
  if (!rpcRes.ok) throw new Error(`rpc ${tool} failed: ${rpcRes.status}`);
  const rpc = await rpcRes.json();
  const jobId = rpc.job_id;
  // Consume SSE briefly to finalize execution and let server write audit
  try {
    const ac = new AbortController();
    const timer = setTimeout(() => ac.abort('timeout'), 2000);
    const sseRes = await fetch(`${url}/mcp/sse?job=${encodeURIComponent(jobId)}`, { signal: ac.signal });
    if (!sseRes.ok) throw new Error('sse not ok');
    const reader = sseRes.body.getReader();
    const td = new TextDecoder();
    let buf = '';
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += td.decode(value, { stream: true });
      const lines = buf.split(/\n/);
      buf = lines.pop() || '';
      for (const ln of lines) {
        if (ln.startsWith('data:')) {
          try {
            const payload = JSON.parse(ln.slice(5).trim());
            if (payload && (payload.event === 'ok' || payload.event === 'fault')) {
              clearTimeout(timer);
              ac.abort('done');
              return { ok: payload.event === 'ok', result: payload.result || null };
            }
          } catch {}
        }
      }
    }
    clearTimeout(timer);
  } catch (e) {
    // Non-fatal: SSE may be cut short; audit likely written already
  }
  return { ok: true };
}

// In-memory subscribers per-origin
const subscribers = new Map(); // origin -> { abort: AbortController }

function pushActivity(activityMap, origin, item) {
  const list = activityMap[origin]?.activity || [];
  const next = [...list, { ts: Date.now(), ...item }].slice(-50);
  const st = activityMap[origin] || {};
  activityMap[origin] = { ...st, activity: next };
}

// Message router (popup/content → background)
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg?.type === 'bridge.state.get') {
      const { origin } = msg;
      const st = await loadState();
      sendResponse({ ok: true, state: st[origin] || {} });
      return;
    }
    if (msg?.type === 'bridge.state.set') {
      const { origin, patch } = msg;
      const st = await loadState();
      const prev = st[origin] || {};
      st[origin] = { ...prev, ...patch };
      await saveState(st);
      sendResponse({ ok: true, state: st[origin] });
      return;
    }
    if (msg?.type === 'config.get') {
      const cfg = await loadConfig();
      sendResponse({ ok: true, config: cfg });
      return;
    }
    if (msg?.type === 'config.set') {
      const cfg = await saveConfig(msg.config || {});
      sendResponse({ ok: true, config: cfg });
      return;
    }
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
      const r = await chrome.tabs.sendMessage(tab.id, { type: 'content.validate', text });
      // Best-effort audit via MCP events.log
      try {
        const origin = originKeyFromUrl(tab.url);
        await mcpCall('events.log', { event: 'validate', origin, observed: Boolean(r?.observed) });
      } catch {}
      sendResponse({ ok: true, observed: r?.observed || null });
      return;
    }
    if (msg?.type === 'bridge.join') {
      const tab = await getActiveTab();
      const ok = !!tab?.url; const origin = ok ? originKeyFromUrl(tab.url) : null;
      if (!ok || !origin) { sendResponse({ ok: false }); return; }
      const { session_id, display_name, avatar } = msg;
      // Generate participant id; persist per-origin in state
      const pid = `WEB-${new URL(tab.url).hostname}-${Math.random().toString(16).slice(2, 8)}`;
      try {
        await mcpCall('participants.register', {
          origin,
          display_name: display_name || (tab.title ? `${tab.title}` : `Web UI @ ${new URL(tab.url).hostname}`),
          avatar: avatar || undefined,
          capabilities: ['send_text', 'recv_text'],
          participant_id: pid,
        });
        await mcpCall('events.log', { event: 'participants.register', origin, participant_id: pid, data: { session_id: session_id || null } });
      } catch {}
      const st = await loadState();
      st[origin] = { ...(st[origin] || {}), participant_id: pid, session_id: session_id || '', display_name, avatar, activity: (st[origin]?.activity || []) };
      await saveState(st);
      sendResponse({ ok: true, origin, participant_id: pid });
      return;
    }
    if (msg?.type === 'bridge.leave') {
      const { origin } = msg;
      const st = await loadState();
      const prev = st[origin] || {};
      st[origin] = { ...prev, participant_id: null };
      await saveState(st);
      sendResponse({ ok: true });
      return;
    }
    if (msg?.type === 'bridge.sendText') {
      const tab = await getActiveTab();
      if (!tab?.id) { sendResponse({ ok: false, error: 'no-active-tab' }); return; }
      const text = msg.text;
      const origin = originKeyFromUrl(tab.url);
      const state = await loadState();
      const pid = state[origin]?.participant_id || null;
      const r = await chrome.tabs.sendMessage(tab.id, { type: 'content.sendText', text });
      try {
        await mcpCall('participants.message', { participant_id: pid || undefined, text, origin });
        await mcpCall('events.log', { event: 'send_text', origin, participant_id: pid || undefined, observed: Boolean(r?.observed) });
      } catch {}
      // Update activity log (outbound)
      pushActivity(state, origin, { dir: 'out', participant_id: pid, text });
      await saveState(state);
      sendResponse({ ok: true, observed: r?.observed || null });
      return;
    }
    if (msg?.type === 'bridge.activity.get') {
      const { origin } = msg;
      const st = await loadState();
      sendResponse({ ok: true, activity: (st[origin]?.activity || []) });
      return;
    }
    if (msg?.type === 'bridge.subscribe.start') {
      const { origin } = msg;
      const st = await loadState();
      const s = st[origin] || {};
      const sessionId = s.session_id;
      if (!sessionId) { sendResponse({ ok: false, error: 'no-session' }); return; }
      if (subscribers.has(origin)) { sendResponse({ ok: true }); return; }
      const { semhostUrl } = await loadConfig();
      const url = (semhostUrl || '').replace(/\/$/, '');
      const ac = new AbortController();
      subscribers.set(origin, { abort: ac });
      (async () => {
        try {
          const res = await fetch(`${url}/sessions/${encodeURIComponent(sessionId)}/stream`, { signal: ac.signal });
          if (!res.ok) throw new Error('subscribe failed');
          const reader = res.body.getReader();
          const td = new TextDecoder();
          let buf = '';
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            buf += td.decode(value, { stream: true });
            const lines = buf.split(/\n/);
            buf = lines.pop() || '';
            for (const ln of lines) {
              if (!ln.startsWith('data:')) continue;
              try {
                const payload = JSON.parse(ln.slice(5).trim());
                if (payload?.event === 'turn_result') {
                  const text = payload?.result?.text || payload?.text || '';
                  const alias = payload?.result?.alias || payload?.alias || '';
                  pushActivity(st, origin, { dir: 'in', alias, text });
                  await saveState(st);
                  // Optionally forward to page in future when toggle is present
                }
              } catch {}
            }
          }
        } catch (e) {
          // swallow; popup may retry
        } finally {
          subscribers.delete(origin);
        }
      })();
      sendResponse({ ok: true });
      return;
    }
    if (msg?.type === 'bridge.subscribe.stop') {
      const { origin } = msg;
      const sub = subscribers.get(origin);
      if (sub) { try { sub.abort.abort('stop'); } catch {} subscribers.delete(origin); }
      sendResponse({ ok: true });
      return;
    }
  })();
  // Indicate async response
  return true;
});
