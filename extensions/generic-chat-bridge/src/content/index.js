// overlay.js injects globals in content-script context
const _overlay = window.__actcliOverlay;
const computeSelector = window.__actcliComputeSelector;

let currentProfile = null; // { input, send, history }
let runningObserver = null;

function getOrigin() {
  return location.origin;
}

function selectEl(sel) {
  try { return document.querySelector(sel); } catch { return null; }
}

function observeHistory(historySel, onAppend) {
  const el = selectEl(historySel);
  if (!el) return null;
  const obs = new MutationObserver(muts => {
    for (const m of muts) {
      if (m.type === 'childList' && m.addedNodes && m.addedNodes.length) {
        const visibleText = Array.from(m.addedNodes)
          .map(n => n.textContent || '')
          .join('\n')
          .trim();
        if (visibleText) onAppend(visibleText);
      }
    }
  });
  obs.observe(el, { childList: true, subtree: true });
  return obs;
}

async function postBackground(msg) {
  return await chrome.runtime.sendMessage(msg);
}

async function validateTextInternal(text) {
  const origin = getOrigin();
  const res = await postBackground({ type: 'bridge.getProfile', origin });
  const prof = res?.profile;
  if (!prof || !prof.input || !prof.send || !prof.history) {
    return { ok: false, error: 'no-profile' };
  }
  const inputEl = selectEl(prof.input);
  const sendEl = selectEl(prof.send);
  const histEl = selectEl(prof.history);
  if (!inputEl || !sendEl || !histEl) {
    return { ok: false, error: 'elements-not-found' };
  }
  try {
    inputEl.focus();
    const before = new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: text });
    inputEl.dispatchEvent(before);
    if ('value' in inputEl) { inputEl.value = (inputEl.value || '') + text; }
    const after = new InputEvent('input', { bubbles: true, cancelable: true, inputType: 'insertText', data: text });
    inputEl.dispatchEvent(after);
  } catch (e) {
    try { document.execCommand('insertText', false, text); } catch (_) {}
  }
  if (runningObserver) { try { runningObserver.disconnect(); } catch {} }
  let observed = '';
  runningObserver = observeHistory(prof.history, (t) => { observed = t; });
  sendEl.click();
  await new Promise(r => setTimeout(r, 800));
  try { runningObserver && runningObserver.disconnect(); } catch {}
  return { ok: true, observed: observed || null };
}

// Picker → receive selections via window.postMessage from overlay
window.addEventListener('message', async (ev) => {
  const data = ev.data;
  if (!data || data.__actcli_pick !== true) return;
  if (!currentProfile) currentProfile = {};
  if (data.stage === 'input') currentProfile.input = data.selector;
  if (data.stage === 'send') currentProfile.send = data.selector;
  if (data.stage === 'history') currentProfile.history = data.selector;
  if (currentProfile.input && currentProfile.send && currentProfile.history) {
    // Persist to background (per-origin)
    await postBackground({ type: 'bridge.saveProfile', origin: getOrigin(), profile: currentProfile });
    // Notify popup for UX (optional)
    // no-op: popup can pull via bridge.getProfile
  }
});

// Handle messages from background/popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg?.type === 'content.picker.start') {
      // reset and start picking
      currentProfile = null;
      _overlay.start();
      sendResponse({ ok: true });
      return;
    }
    if (msg?.type === 'content.health') {
      const origin = getOrigin();
      const res = await postBackground({ type: 'bridge.getProfile', origin });
      const prof = res?.profile;
      if (!prof) { sendResponse({ ok: false, error: 'no-profile' }); return; }
      const inputEl = selectEl(prof.input);
      const sendEl = selectEl(prof.send);
      const histEl = selectEl(prof.history);
      const ok = !!(inputEl && sendEl && histEl);
      sendResponse({ ok });
      return;
    }
    if (msg?.type === 'content.validate') {
      const { text } = msg;
      const r = await validateTextInternal(text);
      sendResponse(r);
      return;
    }
  })();
  return true;
});

// Expose a basic API for manual debugging (in console)
window.__actcli_bridge = {
  computeSelector,
  pick: () => _overlay.start(),
  validate: (text) => validateTextInternal(text),
};
