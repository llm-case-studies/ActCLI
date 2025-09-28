// Helper to build Playground URLs robustly regardless of env settings.
// - If PLAYGROUND_URL already ends with /playground, reuse it.
// - Otherwise, append /playground to the root URL.

export function playgroundBase() {
  const raw = process.env.PLAYGROUND_URL || 'http://127.0.0.1:4400';
  const trimmed = raw.replace(/\/$/, '');
  if (/\/playground$/i.test(trimmed)) return trimmed;
  return `${trimmed}/playground`;
}

export function playgroundUrl(relPath: string) {
  const base = playgroundBase();
  const rel = String(relPath).replace(/^\//, '');
  return `${base}/${rel}`;
}

