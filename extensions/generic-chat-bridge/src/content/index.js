// overlay.js injects globals in content-script context
// Use dynamic access to avoid reference errors during injection

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

async function saveProfile(profile) {
  currentProfile = { ...(currentProfile || {}), ...profile };
  const origin = getOrigin();
  await postBackground({ type: 'bridge.saveProfile', origin, profile: currentProfile });
  return currentProfile;
}

async function validateTextInternal(text) {
  const origin = getOrigin();
  const res = await postBackground({ type: 'bridge.getProfile', origin });
  const prof = res?.profile;
  if (!prof || !prof.input || !prof.history) {
    return { ok: false, error: 'no-profile' };
  }
  const inputEl = selectEl(prof.input);
  const sendSpec = prof.send || '__KEY:Enter__';
  const isKeySpec = typeof sendSpec === 'string' && sendSpec.startsWith('__KEY:');
  const sendEl = !isKeySpec && sendSpec !== '__ENTER__' ? selectEl(sendSpec) : null;
  const histEl = selectEl(prof.history);
  if (!inputEl || !histEl) {
    return { ok: false, error: 'elements-not-found' };
  }
  try {
    inputEl.focus();
    const before = new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: text });
    inputEl.dispatchEvent(before);

    // Handle both regular inputs (with value) and contenteditable elements
    if ('value' in inputEl) {
      inputEl.value = (inputEl.value || '') + text;
    } else if (inputEl.isContentEditable) {
      inputEl.innerText = (inputEl.innerText || '') + text;
    } else {
      inputEl.textContent = (inputEl.textContent || '') + text;
    }

    const after = new InputEvent('input', { bubbles: true, cancelable: true, inputType: 'insertText', data: text });
    inputEl.dispatchEvent(after);
  } catch (e) {
    try { document.execCommand('insertText', false, text); } catch (_) {}
  }
  if (runningObserver) { try { runningObserver.disconnect(); } catch {} }
  let observed = '';
  runningObserver = observeHistory(prof.history, (t) => { observed = t; });
  // Submit via explicit send button or keyboard combo
  try {
    if (sendEl) {
      sendEl.click();
    } else {
      let key = 'Enter';
      let ctrlKey = false, metaKey = false, altKey = false, shiftKey = false;
      if (isKeySpec) {
        const spec = String(sendSpec).slice('__KEY:'.length, -2); // remove prefix and trailing __
        const parts = spec.split('+');
        key = parts[parts.length - 1] || 'Enter';
        for (let i = 0; i < parts.length - 1; i++) {
          const p = parts[i].toLowerCase();
          if (p === 'ctrl' || p === 'control') ctrlKey = true;
          if (p === 'meta' || p === 'cmd' || p === 'command') metaKey = true;
          if (p === 'alt' || p === 'option') altKey = true;
          if (p === 'shift') shiftKey = true;
        }
      }
      const kd = new KeyboardEvent('keydown', { key, code: key, bubbles: true, ctrlKey, metaKey, altKey, shiftKey });
      const ku = new KeyboardEvent('keyup', { key, code: key, bubbles: true, ctrlKey, metaKey, altKey, shiftKey });
      inputEl.dispatchEvent(kd);
      inputEl.dispatchEvent(ku);
      // Fallback: submit nearest form if present
      const form = inputEl.closest && inputEl.closest('form');
      if (form && typeof form.submit === 'function') {
        try { form.submit(); } catch {}
      }
    }
  } catch {}
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
  if (data.stage === 'send') currentProfile.send = data.selector || '__ENTER__';
  if (data.stage === 'history') currentProfile.history = data.selector;
  // Persist incrementally so popup can reflect mapping progress
  await saveProfile(currentProfile);
});

// Handle messages from background/popup
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  (async () => {
    if (msg?.type === 'content.picker.start') {
      // reset and start picking
      currentProfile = null;
      window.__actcliOverlay?.start();
      sendResponse({ ok: true });
      return;
    }
    if (msg?.type === 'content.health') {
      const origin = getOrigin();
      const res = await postBackground({ type: 'bridge.getProfile', origin });
      const prof = res?.profile;
      if (!prof) { sendResponse({ ok: false, error: 'no-profile' }); return; }
      const inputEl = selectEl(prof.input);
      const sendEl = prof.send && prof.send !== '__ENTER__' ? selectEl(prof.send) : null;
      const histEl = selectEl(prof.history);
      const ok = !!(inputEl && histEl); // send is optional (Enter to submit)
      sendResponse({ ok });
      return;
    }
    if (msg?.type === 'content.validate') {
      const { text } = msg;
      const r = await validateTextInternal(text);
      sendResponse(r);
      return;
    }
    if (msg?.type === 'content.injectProfile') {
      const prof = msg.profile || {};
      await saveProfile(prof);
      sendResponse({ ok: true, profile: currentProfile });
      return;
    }
    if (msg?.type === 'content.autoMap') {
      // Heuristic:
      // - Input: find best textbox/search field
      // - History: pick common containers (#search, #rso, role=main/list, aria-live)
      // - Send: use Enter by default
      let inputSel = null, historySel = null;
      try {
        const elIn = (window.__actcliSelectors?.findBest?.(document, 'input')) ||
          document.querySelector('input[type="search"], input[name="q"], textarea, [role="textbox"], [contenteditable="true"]');
        if (elIn) {
          inputSel = window.__actcliSelectors?.pickBestSelector?.(elIn, 'input') || (elIn.id ? `#${elIn.id}` : null);
        }
      } catch {}
      try {
        const histCand = document.querySelector('#search, #rso, [role="main"], [role="list"], [aria-live], [aria-label*="results" i]');
        if (histCand) {
          historySel = window.__actcliSelectors?.pickBestSelector?.(histCand, 'history') || (histCand.id ? `#${histCand.id}` : null);
        }
      } catch {}
      if (!inputSel || !historySel) {
        sendResponse({ ok: false, error: 'auto-map-failed' });
        return;
      }
      const prof = { input: inputSel, send: '__ENTER__', history: historySel };
      await saveProfile(prof);
      sendResponse({ ok: true, profile: prof });
      return;
    }
  })();
  return true;
});

// Create a bridge to communicate between ISOLATED (this) and MAIN (overlay) worlds
function createCrossBridge() {
  // Listen for messages from the main world
  window.addEventListener('message', async (event) => {
    if (event.source !== window || !event.data || event.data.source !== '__actcli_main_to_isolated') {
      return;
    }

    const { method, params, id } = event.data;

    try {
      let result;
      if (method === 'validate') {
        result = await validateTextInternal(params.text);
      } else {
        result = { ok: false, error: 'unknown-method' };
      }

      // Send response back to main world
      window.postMessage({
        source: '__actcli_isolated_to_main',
        id,
        result
      }, '*');
    } catch (error) {
      window.postMessage({
        source: '__actcli_isolated_to_main',
        id,
        error: error.message
      }, '*');
    }
  });
}

// Set up the bridge between isolated and main worlds
createCrossBridge();
