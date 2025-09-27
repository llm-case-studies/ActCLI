// Simple dev-tools style overlay for element picking.
// Injects a Shadow DOM overlay to highlight hovered element, shows a small tooltip.

class PickerOverlay {
  constructor() {
    this._active = false;
    this._stage = 'input'; // 'input' → 'send' → 'history'
    this._root = null;
    this._highlight = null;
    this._tooltip = null;
    this._lastTarget = null;
    this._onClick = this._onClick.bind(this);
    this._onMove = this._onMove.bind(this);
    this._onKey = this._onKey.bind(this);
  }

  mount() {
    if (this._root) return;
    const host = document.createElement('div');
    host.style.position = 'fixed';
    host.style.inset = '0';
    host.style.zIndex = '2147483647';
    host.style.pointerEvents = 'none'; // let events pass through

    const shadow = host.attachShadow({ mode: 'open' });
    const style = document.createElement('style');
    style.textContent = `
      .hl { position: fixed; border: 2px solid #22d3ee; background: rgba(34,211,238,0.1); pointer-events: none; }
      .tip { position: fixed; font: 12px system-ui, -apple-system, sans-serif; color: #0f172a; background: #a5f3fc; border: 1px solid #0891b2; padding: 2px 6px; border-radius: 4px; pointer-events: none; }
    `;
    const el = document.createElement('div');
    const hl = document.createElement('div');
    hl.className = 'hl';
    const tip = document.createElement('div');
    tip.className = 'tip';
    tip.textContent = 'Pick: input';
    shadow.append(style, el, hl, tip);
    document.documentElement.appendChild(host);
    this._root = host;
    this._highlight = hl;
    this._tooltip = tip;
  }

  start() {
    if (this._active) return;
    this.mount();
    this._active = true;
    this._stage = 'input';
    document.addEventListener('mousemove', this._onMove, true);
    document.addEventListener('click', this._onClick, true);
    document.addEventListener('keydown', this._onKey, true);
    this._setTip('Pick: input');
  }

  stop() {
    this._active = false;
    document.removeEventListener('mousemove', this._onMove, true);
    document.removeEventListener('click', this._onClick, true);
    document.removeEventListener('keydown', this._onKey, true);
    if (this._root) {
      this._root.remove();
      this._root = null;
    }
  }

  _setTip(text) {
    if (!this._tooltip) return;
    this._tooltip.textContent = text;
  }

  _onMove(ev) {
    if (!this._active) return;
    const t = document.elementFromPoint(ev.clientX, ev.clientY);
    if (!t || t === this._root) return;
    this._lastTarget = t;
    const r = t.getBoundingClientRect();
    // Use fixed positioning (viewport coords). Do NOT add scroll offsets.
    Object.assign(this._highlight.style, {
      left: `${r.left}px`,
      top: `${r.top}px`,
      width: `${r.width}px`,
      height: `${r.height}px`,
      display: 'block'
    });
    Object.assign(this._tooltip.style, {
      left: `${r.left + 4}px`,
      top: `${Math.max(4, r.top - 22)}px`,
      display: 'block'
    });
  }

  _onClick(ev) {
    if (!this._active) return;
    // prevent page handlers during picking
    ev.stopPropagation();
    ev.preventDefault();
    const el = this._lastTarget || ev.target;
    // Prefer shared selector engine if available
    const kind = this._stage; // 'input' | 'send' | 'history'
    let sel = null;
    try {
      if (window.__actcliSelectors?.pickBestSelector) {
        sel = window.__actcliSelectors.pickBestSelector(el, kind);
      }
    } catch {}
    if (!sel) sel = computeSelector(el);
    const role = el.getAttribute('role') || '';
    let nextStage = null;
    if (this._stage === 'input') nextStage = 'send';
    else if (this._stage === 'send') nextStage = 'history';
    else nextStage = 'done';

    window.postMessage({ __actcli_pick: true, stage: this._stage, selector: sel, role }, '*');

    if (nextStage === 'done') {
      this.stop();
    } else {
      this._stage = nextStage;
      this._setTip(
        this._stage === 'send'
          ? 'Pick: send (press key to use keyboard submit, or click a button)'
          : `Pick: ${this._stage}`
      );
    }
  }

  _onKey(ev) {
    if (!this._active) return;
    if (ev.key === 'Escape') {
      ev.stopPropagation();
      ev.preventDefault();
      this.stop();
      window.postMessage({ __actcli_pick: true, stage: 'cancel' }, '*');
      return;
    }
    // Capture keyboard-based submit at the Send stage (e.g., Enter, Ctrl+Enter)
    if (this._stage === 'send') {
      ev.stopPropagation();
      ev.preventDefault();
      const mods = [];
      if (ev.ctrlKey) mods.push('Ctrl');
      if (ev.metaKey) mods.push('Meta');
      if (ev.altKey) mods.push('Alt');
      if (ev.shiftKey) mods.push('Shift');
      const key = ev.key || 'Enter';
      const combo = mods.length ? `${mods.join('+')}+${key}` : key;
      window.postMessage({ __actcli_pick: true, stage: 'send', selector: `__KEY:${combo}__` }, '*');
      this._stage = 'history';
      this._setTip('Pick: history');
    }
  }
}

// Basic selector generator with ARIA/stable attribute preference.
function computeSelector(el) {
  if (!(el instanceof Element)) return null;
  // Prefer ID
  if (el.id && document.querySelectorAll(`#${CSS.escape(el.id)}`).length === 1) {
    return `#${el.id}`;
  }
  // Prefer data-testid / data-qa
  for (const attr of ['data-testid', 'data-qa']) {
    const v = el.getAttribute(attr);
    if (v && document.querySelectorAll(`[${attr}="${CSS.escape(v)}"]`).length === 1) {
      return `[${attr}="${v}"]`;
    }
  }
  // Role-based
  const role = el.getAttribute('role');
  if (role === 'textbox') {
    return `${el.tagName.toLowerCase()}[role="textbox"]`;
  }
  // Fallback: build a pruned CSS path
  const parts = [];
  let node = el;
  while (node && node.nodeType === 1 && parts.length < 5) {
    const tag = node.tagName.toLowerCase();
    let part = tag;
    if (node.classList.length) {
      const classes = Array.from(node.classList)
        .filter(c => /[a-zA-Z0-9_-]{2,}/.test(c))
        .slice(0, 2);
      if (classes.length) part += '.' + classes.map(CSS.escape).join('.');
    }
    // nth-of-type only if necessary
    const parent = node.parentElement;
    if (parent) {
      const siblings = Array.from(parent.children).filter(ch => ch.tagName === node.tagName);
      if (siblings.length > 1) {
        const idx = siblings.indexOf(node) + 1;
        part += `:nth-of-type(${idx})`;
      }
    }
    parts.unshift(part);
    node = node.parentElement;
    if (node && node === document.body) break;
  }
  return parts.join('>');
}

// Avoid redeclaration errors in frames/repeated injections
if (!window.__actcliOverlay) {
  const _overlay = new PickerOverlay();

  // Expose globals for non-module content script usage
  window.__actcliOverlay = _overlay;
  window.__actcliComputeSelector = computeSelector;

  // Create the main bridge API that the tests will use
  let messageId = 0;
  const pendingMessages = new Map();

  // Listen for responses from isolated world
  window.addEventListener('message', (event) => {
    if (event.source !== window || !event.data || event.data.source !== '__actcli_isolated_to_main') {
      return;
    }

    const { id, result, error } = event.data;
    const pending = pendingMessages.get(id);
    if (pending) {
      pendingMessages.delete(id);
      if (error) {
        pending.reject(new Error(error));
      } else {
        pending.resolve(result);
      }
    }
  });

  // Helper to send messages to isolated world
  function sendToIsolated(method, params) {
    return new Promise((resolve, reject) => {
      const id = ++messageId;
      pendingMessages.set(id, { resolve, reject });

      window.postMessage({
        source: '__actcli_main_to_isolated',
        method,
        params,
        id
      }, '*');

      // Timeout after 10 seconds
      setTimeout(() => {
        if (pendingMessages.has(id)) {
          pendingMessages.delete(id);
          reject(new Error('timeout'));
        }
      }, 10000);
    });
  }

  // Expose the main bridge API
  window.__actcli_bridge = {
    computeSelector,
    pick: () => _overlay.start(),
    validate: (text) => sendToIsolated('validate', { text })
  };
}
