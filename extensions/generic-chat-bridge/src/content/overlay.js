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
    Object.assign(this._highlight.style, {
      left: `${r.left + window.scrollX}px`,
      top: `${r.top + window.scrollY}px`,
      width: `${r.width}px`,
      height: `${r.height}px`,
      display: 'block'
    });
    Object.assign(this._tooltip.style, {
      left: `${r.left + window.scrollX + 4}px`,
      top: `${r.top + window.scrollY - 22}px`,
      display: 'block'
    });
  }

  _onClick(ev) {
    if (!this._active) return;
    // prevent page handlers during picking
    ev.stopPropagation();
    ev.preventDefault();
    const el = this._lastTarget || ev.target;
    const sel = computeSelector(el);
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
      this._setTip(`Pick: ${this._stage}`);
    }
  }

  _onKey(ev) {
    if (!this._active) return;
    if (ev.key === 'Escape') {
      ev.stopPropagation();
      ev.preventDefault();
      this.stop();
      window.postMessage({ __actcli_pick: true, stage: 'cancel' }, '*');
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

const _overlay = new PickerOverlay();

// Expose globals for non-module content script usage
// eslint-disable-next-line no-undef
window.__actcliOverlay = _overlay;
// eslint-disable-next-line no-undef
window.__actcliComputeSelector = computeSelector;
