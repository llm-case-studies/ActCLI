async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function setStatus(text) {
  const el = document.getElementById('status');
  if (el) el.textContent = text;
}

function renderActivity(items) {
  const box = document.getElementById('activity');
  if (!box) return;
  box.innerHTML = '';
  (items || []).slice(-20).forEach(it => {
    const div = document.createElement('div');
    const dir = it.dir === 'out' ? '→' : '←';
    const who = it.alias || it.participant_id || 'unknown';
    const t = (it.text || '').replace(/\n/g, ' ');
    div.textContent = `${dir} ${who}: ${t}`;
    box.appendChild(div);
  });
  box.scrollTop = box.scrollHeight;
}

async function refreshLinkStatus() {
  try {
    const tab = await getActiveTab();
    if (!tab?.id) { return; }
    const [h, profRes] = await Promise.all([
      chrome.tabs.sendMessage(tab.id, { type: 'content.health' }).catch(() => null),
      (async () => {
        const origin = tab?.url ? new URL(tab.url).origin : null;
        if (!origin) return null;
        return await chrome.runtime.sendMessage({ type: 'bridge.getProfile', origin });
      })()
    ]);
    const ok = h?.ok;
    const healthEl = document.getElementById('healthStatus');
    if (healthEl) healthEl.textContent = ok ? 'OK' : 'Not Linked';
    const prof = profRes?.profile || null;
    const chip = (id, label, val) => {
      const el = document.getElementById(id);
      if (!el) return;
      const v = val ? String(val) : '—';
      el.textContent = `${label}: ${v}`;
      el.title = v;
    };
    chip('chipInput', 'Input', prof?.input || null);
    chip('chipSend', 'Send', prof?.send || '__ENTER__');
    chip('chipHistory', 'History', prof?.history || null);
    // Link is optional; do not gate send button on link health
  } catch {}
}

async function init() {
  // Load config
  try {
    const r = await chrome.runtime.sendMessage({ type: 'config.get' });
    document.getElementById('semhost').value = r?.config?.semhostUrl || 'http://127.0.0.1:7530';
  } catch {}

  // Load state
  try {
    const tab = await getActiveTab();
    const origin = tab?.url ? new URL(tab.url).origin : null;
    if (origin) {
      const st = await chrome.runtime.sendMessage({ type: 'bridge.state.get', origin });
      const s = st?.state || {};
      if (s.session_id) document.getElementById('sessionId').value = s.session_id;
      if (s.display_name) document.getElementById('displayName').value = s.display_name;
      if (s.avatar) document.getElementById('avatar').value = s.avatar;
    }
  } catch {}

  document.getElementById('saveCfg').addEventListener('click', async () => {
    const semhostUrl = document.getElementById('semhost').value.trim();
    await chrome.runtime.sendMessage({ type: 'config.set', config: { semhostUrl } });
    setStatus('Saved Semhost URL');
  });

  // Session join/leave
  document.getElementById('join').addEventListener('click', async () => {
    const tab = await getActiveTab();
    const origin = tab?.url ? new URL(tab.url).origin : null;
    if (!origin) { setStatus('No active tab/origin'); return; }
    const session_id = document.getElementById('sessionId').value.trim();
    const display_name = document.getElementById('displayName').value.trim() || 'Web Participant';
    const avatar = document.getElementById('avatar').value.trim() || '';
    setStatus('Joining…');
    const r = await chrome.runtime.sendMessage({ type: 'bridge.join', origin, session_id, display_name, avatar });
    if (r?.ok) {
      setStatus('Joined seminar');
      await chrome.runtime.sendMessage({ type: 'bridge.subscribe.start', origin });
    } else {
      setStatus('Join failed');
    }
  });
  document.getElementById('leave').addEventListener('click', async () => {
    const tab = await getActiveTab();
    const origin = tab?.url ? new URL(tab.url).origin : null;
    if (!origin) { setStatus('No active tab/origin'); return; }
    await chrome.runtime.sendMessage({ type: 'bridge.subscribe.stop', origin });
    await chrome.runtime.sendMessage({ type: 'bridge.leave', origin });
    setStatus('Left seminar');
  });

  // Compose send
  async function doSend() {
    const text = document.getElementById('composeText').value;
    if (!text?.trim()) return;
    setStatus('Sending…');
    const r = await chrome.runtime.sendMessage({ type: 'bridge.sendText', text });
    if (r?.ok) {
      setStatus('Sent');
      document.getElementById('composeText').value = '';
    } else {
      setStatus('Send failed');
    }
  }
  document.getElementById('sendNow').addEventListener('click', doSend);
  document.getElementById('composeText').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); doSend(); }
  });

  // Link page actions
  document.getElementById('pick').addEventListener('click', async () => {
    setStatus('Pick: click Input → Send (Enter to skip) → History');
    await chrome.runtime.sendMessage({ type: 'bridge.pickStart' });
  });
  document.getElementById('validate').addEventListener('click', async () => {
    setStatus('Validating…');
    const text = 'Hello from ActCLI';
    const r = await chrome.runtime.sendMessage({ type: 'bridge.validate', text });
    if (r?.ok) setStatus('Validate OK' + (r.observed ? ' (observed)' : ''));
    else setStatus('Validate failed: ' + (r?.error || 'unknown'));
    await refreshLinkStatus();
  });
  document.getElementById('health').addEventListener('click', async () => {
    await refreshLinkStatus();
    setStatus('Checked link');
  });
  document.getElementById('autoMap').addEventListener('click', async () => {
    const tab = await getActiveTab();
    if (!tab?.id) { setStatus('No active tab'); return; }
    setStatus('Auto‑linking…');
    const r = await chrome.tabs.sendMessage(tab.id, { type: 'content.autoMap' });
    if (r?.ok) setStatus('Auto‑link OK'); else setStatus('Auto‑link failed');
    await refreshLinkStatus();
  });
  document.getElementById('export').addEventListener('click', async () => {
    const tab = await getActiveTab();
    const origin = tab?.url ? new URL(tab.url).origin : null;
    if (!origin) { setStatus('Export: no origin'); return; }
    const r = await chrome.runtime.sendMessage({ type: 'bridge.getProfile', origin });
    const profile = r?.profile || {};
    const blob = new Blob([JSON.stringify({ origin, profile }, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = `actcli-link-${(new URL(tab.url)).hostname}.json`;
    a.click(); setStatus('Exported link');
    setTimeout(() => URL.revokeObjectURL(url), 500);
  });
  document.getElementById('import').addEventListener('click', async () => {
    const input = document.createElement('input');
    input.type = 'file'; input.accept = 'application/json';
    input.onchange = async () => {
      const f = input.files?.[0]; if (!f) return;
      try {
        const txt = await f.text();
        const data = JSON.parse(txt);
        const profile = data.profile || data;
        const tab = await getActiveTab();
        const origin = tab?.url ? new URL(tab.url).origin : null;
        if (!origin) { setStatus('Import failed: no origin'); return; }
        await chrome.runtime.sendMessage({ type: 'bridge.saveProfile', origin, profile });
        setStatus('Imported link');
        await refreshLinkStatus();
      } catch (e) {
        setStatus('Import failed: invalid JSON');
      }
    };
    input.click();
  });

  // Periodic refresh
  setInterval(async () => {
    try {
      const tab = await getActiveTab();
      const origin = tab?.url ? new URL(tab.url).origin : null;
      if (!origin) return;
      const a = await chrome.runtime.sendMessage({ type: 'bridge.activity.get', origin });
      renderActivity(a?.activity || []);
    } catch {}
  }, 1500);

  await refreshLinkStatus();
}

document.addEventListener('DOMContentLoaded', init);
