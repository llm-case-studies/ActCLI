function originKeyFromUrl(url) { try { return new URL(url).origin; } catch { return null; } }
async function getActiveTab() { const [tab] = await chrome.tabs.query({ active: true, currentWindow: true }); return tab; }
function setStatus(text) { document.getElementById('status').textContent = text; }

// Load config
(async () => {
  try {
    const r = await chrome.runtime.sendMessage({ type: 'config.get' });
    document.getElementById('semhost').value = r?.config?.semhostUrl || 'http://127.0.0.1:7530';
  } catch {}
})();

document.getElementById('saveCfg').addEventListener('click', async () => {
  const semhostUrl = document.getElementById('semhost').value.trim();
  await chrome.runtime.sendMessage({ type: 'config.set', config: { semhostUrl } });
  setStatus('Saved Semhost URL');
});

document.getElementById('pick').addEventListener('click', async () => {
  setStatus('Picking: click Input → Send → History');
  await chrome.runtime.sendMessage({ type: 'bridge.pickStart' });
});

document.getElementById('validate').addEventListener('click', async () => {
  setStatus('Validating…');
  const text = document.getElementById('testText').value || 'Hello from ActCLI';
  const r = await chrome.runtime.sendMessage({ type: 'bridge.validate', text });
  if (r?.ok) setStatus('Validate: OK' + (r.observed ? ' (observed history append)' : ''));
  else setStatus('Validate failed: ' + (r?.error || 'unknown'));
});

document.getElementById('health').addEventListener('click', async () => {
  setStatus('Health…');
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) { setStatus('No active tab'); return; }
  const ok = await chrome.tabs.sendMessage(tab.id, { type: 'content.health' });
  setStatus(ok?.ok ? 'Health: OK' : 'Health: missing elements or profile');
});

document.getElementById('connect').addEventListener('click', async () => {
  setStatus('Connecting…');
  const r = await chrome.runtime.sendMessage({ type: 'bridge.connect' });
  if (r?.ok) setStatus('Connected for origin: ' + (r.origin || '(unknown)'));
  else setStatus('Connect failed');
});

document.getElementById('disconnect').addEventListener('click', async () => {
  const tab = await getActiveTab();
  const origin = tab?.url ? originKeyFromUrl(tab.url) : null;
  if (origin) await chrome.runtime.sendMessage({ type: 'bridge.deleteProfile', origin });
  setStatus('Disconnected (profile cleared)');
});

document.getElementById('export').addEventListener('click', async () => {
  const tab = await getActiveTab();
  const origin = tab?.url ? originKeyFromUrl(tab.url) : null;
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
      const origin = tab?.url ? originKeyFromUrl(tab.url) : null;
      if (!origin) { setStatus('Import failed: no origin'); return; }
      await chrome.runtime.sendMessage({ type: 'bridge.saveProfile', origin, profile });
      setStatus('Imported profile');
    } catch (e) {
      setStatus('Import failed: invalid JSON');
    }
  };
  input.click();
});