async function getActiveTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

function setStatus(text) {
  const el = document.getElementById('status');
  if (el) el.textContent = text;
}

async function refreshConnectState() {
  try {
    const tab = await getActiveTab();
    const btn = document.getElementById('connect');
    if (!tab?.id) { btn?.setAttribute('disabled', 'true'); return; }
    const h = await chrome.tabs.sendMessage(tab.id, { type: 'content.health' });
    if (h?.ok) btn?.removeAttribute('disabled'); else btn?.setAttribute('disabled', 'true');
  } catch {
    const btn = document.getElementById('connect');
    btn?.setAttribute('disabled', 'true');
  }
}

async function init() {
  // Load config
  try {
    const r = await chrome.runtime.sendMessage({ type: 'config.get' });
    document.getElementById('semhost').value = r?.config?.semhostUrl || 'http://127.0.0.1:7530';
  } catch {}

  document.getElementById('saveCfg').addEventListener('click', async () => {
    const semhostUrl = document.getElementById('semhost').value.trim();
    await chrome.runtime.sendMessage({ type: 'config.set', config: { semhostUrl } });
    setStatus('Saved Semhost URL');
  });

  document.getElementById('pick').addEventListener('click', async () => {
    setStatus('Picking: click Input → Send (Enter to skip) → History');
    await chrome.runtime.sendMessage({ type: 'bridge.pickStart' });
  });

  document.getElementById('validate').addEventListener('click', async () => {
    setStatus('Validating…');
    const text = document.getElementById('testText').value || 'Hello from ActCLI';
    const r = await chrome.runtime.sendMessage({ type: 'bridge.validate', text });
    if (r?.ok) setStatus('Validate: OK' + (r.observed ? ' (observed history append)' : ''));
    else setStatus('Validate failed: ' + (r?.error || 'unknown'));
    await refreshConnectState();
  });

  document.getElementById('health').addEventListener('click', async () => {
    setStatus('Health…');
    const tab = await getActiveTab();
    if (!tab?.id) { setStatus('No active tab'); return; }
    const ok = await chrome.tabs.sendMessage(tab.id, { type: 'content.health' });
    setStatus(ok?.ok ? 'Health: OK' : 'Health: missing input/history or profile');
    await refreshConnectState();
  });

  document.getElementById('autoMap').addEventListener('click', async () => {
    const tab = await getActiveTab();
    if (!tab?.id) { setStatus('No active tab'); return; }
    setStatus('Auto-mapping…');
    const r = await chrome.tabs.sendMessage(tab.id, { type: 'content.autoMap' });
    if (r?.ok) setStatus('Auto-map OK'); else setStatus('Auto-map failed');
    await refreshConnectState();
  });

  document.getElementById('connect').addEventListener('click', async () => {
    const tab = await getActiveTab();
    if (!tab?.id) { setStatus('No active tab'); return; }
    // Require mapped page (health OK) before connecting
    const h = await chrome.tabs.sendMessage(tab.id, { type: 'content.health' });
    if (!h?.ok) { setStatus('Map page first: Pick + Health must be OK'); return; }
    setStatus('Connecting…');
    const r = await chrome.runtime.sendMessage({ type: 'bridge.connect' });
    if (r?.ok) setStatus('Connected for origin: ' + (r.origin || '(unknown)'));
    else setStatus('Connect failed');
  });

  document.getElementById('disconnect').addEventListener('click', async () => {
    const tab = await getActiveTab();
    const origin = tab?.url ? new URL(tab.url).origin : null;
    if (origin) await chrome.runtime.sendMessage({ type: 'bridge.deleteProfile', origin });
    setStatus('Disconnected (profile cleared)');
    await refreshConnectState();
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
    a.href = url; a.download = `actcli-bridge-${(new URL(tab.url)).hostname}.json`;
    a.click(); setStatus('Exported profile');
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
        setStatus('Imported profile');
        await refreshConnectState();
      } catch (e) {
        setStatus('Import failed: invalid JSON');
      }
    };
    input.click();
  });

  await refreshConnectState();
}

document.addEventListener('DOMContentLoaded', init);
