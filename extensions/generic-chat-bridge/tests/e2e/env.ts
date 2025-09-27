// Lightweight .env loader for PW specs
// Loads variables from ../../docker/.env if present and not already set.

import fs from 'fs';
import path from 'path';

export function loadDotEnv() {
  try {
    const p = path.resolve(__dirname, '../../docker/.env');
    if (!fs.existsSync(p)) return;
    const text = fs.readFileSync(p, 'utf-8');
    for (const raw of text.split(/\r?\n/)) {
      const line = raw.trim();
      if (!line || line.startsWith('#')) continue;
      const eq = line.indexOf('=');
      if (eq <= 0) continue;
      const key = line.slice(0, eq).trim();
      const val = line.slice(eq + 1).trim();
      if (!process.env[key]) process.env[key] = val;
    }
  } catch {
    // ignore
  }
}

