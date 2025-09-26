// ActCLI Web Bridge — Selector Engine (A2)
// Heuristics for generating and scoring resilient selectors with ARIA-first priority.

(function(){
  const KEYWORDS = {
    input: ['message', 'compose', 'type', 'chat'],
    send: ['send', 'reply', 'submit'],
    history: ['history', 'messages', 'thread']
  };

  function norm(s){ return String(s || '').trim().toLowerCase(); }

  function textMatches(el, keywords){
    const aria = norm(el.getAttribute('aria-label'));
    const title = norm(el.getAttribute('title'));
    const ph = norm(el.getAttribute('placeholder'));
    const text = norm(el.textContent || '');
    return keywords.some(k => aria.includes(k) || title.includes(k) || ph.includes(k) || text.includes(k));
  }

  function isInputCandidate(el){
    if (!(el instanceof Element)) return false;
    if (el.matches('textarea, input[type="text"], input:not([type])')) return true;
    if (el.getAttribute('contenteditable') === 'true') return true;
    if (el.getAttribute('role') === 'textbox') return true;
    return false;
  }

  function isSendCandidate(el){
    if (!(el instanceof Element)) return false;
    if (el.matches('button, [role="button"]')) return textMatches(el, KEYWORDS.send) || true;
    if (textMatches(el, KEYWORDS.send)) return true;
    return false;
  }

  function isHistoryCandidate(el){
    if (!(el instanceof Element)) return false;
    if (el.getAttribute('role') === 'list' || el.getAttribute('role') === 'log') return true;
    if (textMatches(el, KEYWORDS.history)) return true;
    return false;
  }

  function uniq(sel){
    try { return document.querySelectorAll(sel).length === 1; } catch { return false; }
  }

  function idSelector(el){
    const id = el.id;
    if (id && uniq(`#${CSS.escape(id)}`)) return `#${id}`;
    return null;
  }
  function dataSelector(el){
    for (const a of ['data-testid', 'data-qa']){
      const v = el.getAttribute(a);
      if (v){ const sel = `[${a}="${CSS.escape(v)}"]`; if (uniq(sel)) return sel; }
    }
    return null;
  }
  function roleSelector(el, kind){
    const role = el.getAttribute('role');
    if (kind === 'input' && role === 'textbox') return `${el.tagName.toLowerCase()}[role="textbox"]`;
    if (kind === 'send' && role === 'button') return `${el.tagName.toLowerCase()}[role="button"]`;
    if (kind === 'history' && (role === 'list' || role === 'log')) return `${el.tagName.toLowerCase()}[role="${role}"]`;
    return null;
  }
  function prunedPath(el){
    const parts = [];
    let node = el;
    while (node && node !== document.body && parts.length < 5){
      let part = node.tagName.toLowerCase();
      if (node.classList && node.classList.length){
        const cls = Array.from(node.classList).filter(c => /[\w-]{3,}/.test(c)).slice(0,2);
        if (cls.length) part += '.' + cls.map(CSS.escape).join('.');
      }
      const p = node.parentElement;
      if (p){
        const sibs = Array.from(p.children).filter(ch => ch.tagName === node.tagName);
        if (sibs.length > 1){ part += `:nth-of-type(${sibs.indexOf(node)+1})`; }
      }
      parts.unshift(part);
      node = node.parentElement;
    }
    return parts.join('>');
  }

  function neighborScore(el, kind){
    // Up to 2 ancestors, search siblings/desc for complementary elements
    let node = el;
    for (let depth=0; node && depth<3; depth++){
      const scope = node;
      if (kind === 'input' && scope.querySelector && scope.querySelector('button, [role="button"]')) return 8;
      if (kind === 'send' && scope.querySelector && scope.querySelector('textarea, [role="textbox"], [contenteditable="true"]')) return 8;
      if (kind === 'history' && scope.querySelector && scope.querySelector('[role="list"], [role="log"]')) return 6;
      node = node.parentElement;
    }
    return 0;
  }

  function scoreCandidate(el, kind){
    let score = 0;
    if (kind === 'input' && isInputCandidate(el)) score += 30;
    if (kind === 'send' && isSendCandidate(el)) score += 30;
    if (kind === 'history' && isHistoryCandidate(el)) score += 30;
    const idSel = idSelector(el); if (idSel) score += 70;
    const dataSel = dataSelector(el); if (dataSel) score += 60;
    const roleSel = roleSelector(el, kind); if (roleSel) score += 50;
    if (kind === 'input' && textMatches(el, KEYWORDS.input)) score += 10;
    if (kind === 'send' && textMatches(el, KEYWORDS.send)) score += 10;
    if (kind === 'history' && textMatches(el, KEYWORDS.history)) score += 8;
    score += neighborScore(el, kind);
    // Penalize deep/nth-of-type heavy paths
    const path = prunedPath(el);
    if (/:nth-of-type\(/.test(path)) score -= 10;
    if (path.split('>').length > 4) score -= 5;
    return score;
  }

  function pickBestSelector(el, kind){
    // Choose highest-confidence unique selector
    const candidates = [];
    const idSel = idSelector(el); if (idSel) candidates.push({ sel: idSel, w: 100 });
    const dataSel = dataSelector(el); if (dataSel) candidates.push({ sel: dataSel, w: 90 });
    const roleSel = roleSelector(el, kind); if (roleSel) candidates.push({ sel: roleSel, w: 80 });
    const pathSel = prunedPath(el); if (pathSel) candidates.push({ sel: pathSel, w: 60 });
    // Adjust by neighbor score
    const n = neighborScore(el, kind);
    for (const c of candidates) c.w += n;
    candidates.sort((a,b) => b.w - a.w);
    for (const c of candidates){ if (uniq(c.sel)) return c.sel; }
    // fallback allow non-unique best
    return candidates.length ? candidates[0].sel : null;
  }

  function findBest(doc, kind){
    const root = doc || document;
    const all = Array.from(root.querySelectorAll('*')).slice(0, 2000);
    let best = null; let bestScore = -1;
    for (const el of all){
      const s = scoreCandidate(el, kind);
      if (s > bestScore){ best = el; bestScore = s; }
    }
    return best;
  }

  const api = {
    scoreCandidate, pickBestSelector, findBest,
    _internals: { idSelector, dataSelector, roleSelector, prunedPath, isInputCandidate, isSendCandidate, isHistoryCandidate }
  };
  // Expose globally for content scripts and tests
  window.__actcliSelectors = api;
})();

