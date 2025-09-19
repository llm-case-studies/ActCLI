from __future__ import annotations

import http.server
import os
import socketserver
import threading
import webbrowser
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel


console = Console()


INDEX_HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1"/>
    <title>ActCLI Presenter</title>
    <link rel="stylesheet" href="style.css"/>
  </head>
  <body>
    <header>
      <h1>ActCLI Presenter</h1>
      <div id="meta"></div>
    </header>
    <main>
      <section id="prompt"></section>
      <section id="responses"></section>
      <section id="synthesis"></section>
    </main>
    <script src="app.js"></script>
  </body>
  </html>
"""

STYLE_CSS = """
body { font-family: system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background: #0b0c10; color: #e5e7eb; }
header { background: #111827; padding: 12px 16px; border-bottom: 1px solid #1f2937; }
h1 { margin: 0; font-size: 18px; color: #a7f3d0; }
#meta { color: #9ca3af; font-size: 12px; }
main { padding: 16px; }
section { margin-bottom: 16px; }
.card { background: #111827; border: 1px solid #1f2937; border-radius: 6px; padding: 12px; margin-bottom: 12px; }
.model { color: #93c5fd; }
.error { color: #fca5a5; }
"""

APP_JS = """
async function loadState() {
  try {
    const res = await fetch('state.json', { cache: 'no-store' });
    if (!res.ok) return;
    const s = await res.json();
    document.getElementById('meta').textContent = new Date(s.timestamp).toLocaleString();
    document.getElementById('prompt').innerHTML = `<div class="card"><strong>Prompt</strong><div>${escapeHtml(s.prompt || '')}</div></div>`;
    const respEl = document.getElementById('responses');
    respEl.innerHTML = '';
    (s.results || []).forEach(r => {
      const div = document.createElement('div');
      div.className = 'card';
      const header = `<div><span class="model">${r.name}</span> • ${r.latency_ms} ms ${r.local ? '• local' : ''}</div>`;
      const body = r.text ? `<div>${escapeHtml(r.text)}</div>` : `<div class="error">${escapeHtml(r.error || 'no output')}</div>`;
      div.innerHTML = header + body;
      respEl.appendChild(div);
    });
    const synEl = document.getElementById('synthesis');
    synEl.innerHTML = s.synthesis ? `<div class="card"><strong>Synthesis</strong><div>${escapeHtml(s.synthesis)}</div></div>` : '';
  } catch (e) { /* ignore */ }
}
function escapeHtml(str) { return (str || '').replace(/[&<>]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;'}[c])); }
setInterval(loadState, 1500);
loadState();
"""


def prepare_presenter(out_dir: Path) -> Path:
    root = out_dir / "presenter"
    root.mkdir(parents=True, exist_ok=True)
    (root / "index.html").write_text(INDEX_HTML, encoding="utf-8")
    (root / "style.css").write_text(STYLE_CSS, encoding="utf-8")
    (root / "app.js").write_text(APP_JS, encoding="utf-8")
    return root


def start_presenter(port: int = 8765, open_browser: bool = True) -> None:
    root = prepare_presenter(Path("out"))
    os.chdir(root)
    handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("127.0.0.1", port), handler) as httpd:
        url = f"http://127.0.0.1:{port}/"
        console.print(Panel(f"Presenter serving {root}\nURL: {url}", title="Presenter", border_style="cyan"))
        if open_browser:
            try:
                webbrowser.open(url)
            except Exception:
                pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            console.print("Stopping presenter…")

