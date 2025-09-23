# CLI Playground (Experiments)

This folder contains small, opt-in scripts to explore CLI-based model integrations and behaviors without impacting core code.

Contents
- `codex_cli_models_probe.py` — Probes Codex CLI model selection capabilities across versions and reports the best invocation.
- `gemini_cli_shim.py` — A minimal shim to emulate a Gemini CLI using Python. It can be wired to real APIs (GOOGLE_API_KEY) or stubbed for demos.

Notes
- These scripts are best-effort helpers; they do not run in automated tests.
- Use a short timeout first to prevent long blocking calls.

