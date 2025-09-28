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

function flashEl(el, color = '#22d3ee') {
  try {
    if (!el || !(el instanceof HTMLElement)) return;
    const prev = { outline: el.style.outline, transition: el.style.transition };
    el.style.transition = 'outline .15s ease';
    let n = 0;
    const id = setInterval(() => {
      el.style.outline = n++ % 2 ? `3px solid ${color}` : 'none';
    }, 180);
    setTimeout(() => {
      clearInterval(id);
      el.style.outline = prev.outline || '';
      el.style.transition = prev.transition || '';
    }, 1200);
  } catch {}
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

async function validateTextInternal(text, options = {}) {
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
    inputEl.scrollIntoView({ block: 'center', inline: 'nearest' });
    inputEl.focus();
    // Visual hint to confirm selected input
    flashEl(inputEl);

    // Robust insertion for input and contenteditable
    const tryInsert = () => {
      try {
        const before = new InputEvent('beforeinput', { bubbles: true, cancelable: true, inputType: 'insertText', data: text });
        inputEl.dispatchEvent(before);
      } catch {}
      if ('value' in inputEl) {
        try { inputEl.value = (inputEl.value || '') + text; } catch {}
      } else if (inputEl.isContentEditable) {
        try { inputEl.innerText = (inputEl.innerText || '') + text; } catch {}
        if (!inputEl.innerText || !inputEl.innerText.includes(text)) {
          try { document.execCommand('insertText', false, text); } catch {}
        }
        if (!inputEl.innerText || !inputEl.innerText.includes(text)) {
          try {
            const sel = window.getSelection && window.getSelection();
            const range = document.createRange();
            range.selectNodeContents(inputEl);
            range.collapse(false);
            sel && sel.removeAllRanges();
            sel && sel.addRange(range);
            document.execCommand('insertText', false, text);
          } catch {}
        }
        if (!inputEl.innerText || !inputEl.innerText.includes(text)) {
          try { inputEl.textContent = (inputEl.textContent || '') + text; } catch {}
        }
      } else {
        try { inputEl.textContent = (inputEl.textContent || '') + text; } catch {}
      }
      try {
        const after = new InputEvent('input', { bubbles: true, cancelable: true, inputType: 'insertText', data: text });
        inputEl.dispatchEvent(after);
      } catch {}
    };

    // Initial attempt
    tryInsert();
    // Ensure text persists; if not, append a text node as a final fallback
    for (let i = 0; i < 4; i++) {
      if ((inputEl.value && String(inputEl.value).includes(text)) || (inputEl.innerText && inputEl.innerText.includes(text)) || (inputEl.textContent && inputEl.textContent.includes(text))) {
        break;
      }
      tryInsert();
      await new Promise(r => setTimeout(r, 120));
    }
    if (!((inputEl.value && String(inputEl.value).includes(text)) || (inputEl.innerText && inputEl.innerText.includes(text)) || (inputEl.textContent && inputEl.textContent.includes(text)))) {
      try {
        const tn = document.createTextNode(text);
        inputEl.appendChild(tn);
      } catch {}
    }
  } catch (e) {
    try { document.execCommand('insertText', false, text); } catch (_) {}
  }
  // If debugging is requested, allow holding the text in the input without submitting
  const holdMs = Number(options?.holdMs || 0) || Number(prof?.debug_hold_input_ms || 0) || 0;
  const noSubmit = Boolean(options?.noSubmit) || Boolean(prof?.debug_no_submit);

  if (runningObserver) { try { runningObserver.disconnect(); } catch {} }
  let observed = '';
  runningObserver = observeHistory(prof.history, (t) => { observed = t; });

  if (noSubmit || holdMs > 0) {
    // Keep text visible; do not press Enter or click send
    if (holdMs > 0) {
      const end = Date.now() + holdMs;
      while (Date.now() < end) {
        try {
          if (inputEl && inputEl.isConnected) {
            // Reassert text to fight any stray clears
            if ('value' in inputEl) {
              if (!String(inputEl.value || '').includes(text)) inputEl.value = (inputEl.value || '') + text;
            } else if (inputEl.isContentEditable) {
              if (!String(inputEl.innerText || '').includes(text)) inputEl.innerText = (inputEl.innerText || '') + text;
            } else if (!String(inputEl.textContent || '').includes(text)) {
              inputEl.textContent = (inputEl.textContent || '') + text;
            }
          }
        } catch {}
        await new Promise(r => setTimeout(r, 200));
      }
    }
    try { runningObserver && runningObserver.disconnect(); } catch {}
    return { ok: true, observed: null, held: true };
  }

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

  // Best-effort: if a virtualization viewport exists, scroll it to bottom to trigger render
  try {
    const vp = document.querySelector('#viewport');
    if (vp && 'scrollTop' in vp && 'scrollHeight' in vp) {
      vp.scrollTop = vp.scrollHeight;
      try { vp.dispatchEvent(new Event('scroll', { bubbles: true })); } catch {}
    }
  } catch {}

  await new Promise(r => setTimeout(r, 800));
  // If nothing observed yet, try a conservative click on a send-like button
  if (!observed) {
    try {
      const cand = document.querySelector('#send, button#send, [aria-label="Send"], button[title="Send"]');
      if (cand) {
        flashEl(cand, '#10b981');
        cand.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
        await new Promise(r => setTimeout(r, 400));
      }
    } catch {}
  }
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
      // Flash mapped elements to confirm selection visually
      try {
        const inEl = prof.input ? selectEl(prof.input) : null;
        const hsEl = prof.history ? selectEl(prof.history) : null;
        flashEl(inEl);
        setTimeout(() => flashEl(hsEl, '#f59e0b'), 200);
      } catch {}
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
        result = await validateTextInternal(params.text, params);
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
