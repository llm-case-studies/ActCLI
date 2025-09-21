# Providers, Auth, and CLI-backed Models

This guide summarizes how ActCLI can run models via two tracks:

- API-backed (keys/tokens): OpenAI, Anthropic, Google (Gemini)
- CLI-backed (subscription login handled by the vendor CLI): Codex (OpenAI), Claude CLI (Anthropic)

It also covers listing models, checking provider readiness, and the new unlimited rounds features.

## Two Ways to Use Cloud Models

- API keys (fastest for engineering teams)
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`
  - Verify: `actcli auth status`
  - List: `actcli models list --provider openai|anthropic|google --refresh`

- Vendor CLIs (great for “bring your subscription”)
  - Codex CLI (OpenAI): `npm i -g @openai/codex` (or `brew install codex`), then run `codex` and sign in.
  - Claude CLI (Anthropic): `npm i -g @anthropic-ai/claude-code`, then run `claude` and sign in.
  - In ActCLI:
    - Inspect CLI providers: `actcli providers doctor`
    - Launch login from ActCLI: `actcli providers login codex_cli` or `actcli providers login claude_cli`

## Codex CLI — Model & Reasoning Selection (Docs + Practical)

- Official docs (model switching + reasoning levels):
  - Codex CLI page: https://developers.openai.com/codex/cli/
  - GPT‑5 developer post (verbosity + reasoning_effort minimal/low/medium/high): https://openai.com/index/introducing-gpt-5-for-developers/
  - Help Center (non‑interactive model flag examples): https://help.openai.com/en/articles/11096431-openai-codex-cli-getting-started
- How to switch models interactively:
  - `codex /model` → choose among "gpt‑5 minimal/low/medium/high" or switch to "gpt‑5-codex" or fast options like "gpt‑4o-mini".
- How to set models non‑interactively (varies by version):
  - `codex exec --model gpt-4o-mini "Prompt…"`
  - `codex --model gpt-4o-mini "Prompt…"`
  - Pre‑switch for the session then exec: `codex /model gpt-4o-mini` → `codex exec "Prompt…"`
- ActCLI adapter behavior (as of Sprint 3):
  - We attempt, in order: `exec --model`, top‑level `--model`, then a pre‑switch via `/model` before falling back to default.
  - In seminar participant specs, set `model_id` to a fast model, e.g. `{"provider":"codex_cli","model_id":"gpt-4o-mini"}`.
  - If your Codex build supports a reasoning flag explicitly, we can extend the adapter to pass it (today, the `/model` menu controls minimal/low/medium/high).

Recommended profiles for seminars (speed‑optimized):
- `gpt-4o-mini` (fast generalist)
- `gpt-5-codex` (coding‑oriented, generally faster than deep reasoning)
- `gpt-5 minimal` or `low` (via `/model`) for shorter latency

## Listing Models

- Local (Ollama): `actcli models list` (defaults to `http://127.0.0.1:11435`)
- Aggregated cloud + CLI view: `actcli models list --provider all`
  - Columns:
    - Provider: `ollama`, `openai`, `anthropic`, `google`, `claude_cli`, `codex_cli`
    - Source: `local`, `cloud(api)`, `cloud(cli)`
    - Auth: `local`, `env`, `cli`, or `none`
- Per-provider:
  - `actcli models list --provider codex_cli` (shows “default (via CLI)”) — switch via `codex /model`
  - `actcli models list --provider claude_cli` (published aliases + known ids)

## Running the Roundtable

- Offline-first (safe): `actcli chat --multi "A=echo,B=echo"`
- With CLI-backed Codex + Echo:
  - `actcli chat --multi "codex_cli:default,echo"`
  - In REPL: `/share cloud on`
  - Type your prompt; each round every participant “speaks” once.
- With Gemini (API key):
  - `export GOOGLE_API_KEY=...`
  - `actcli chat --multi "gemini,echo"` then `/share cloud on`

## Unlimited Rounds & Controls

- Slash commands (REPL):
  - `/round start` • `/round next` • `/round stop` • `/round status`
  - `/round max <N>` • `/round window <K>` (context window)
  - `/temp [alias] <0.0–1.0>` • `/mood [alias] <cautious|creative|friday>`
  - `/params show` • `/focus <alias1,alias2>` (subset for next round)
- Persistence: `out/sessions/<id>/session.json` and `round-<n>.json`
- Details/spec: see `docs/Seminar_Rounds_Spec.md`

## Experiments: Gemini Auth Playground

In `experiments/oauth-playground/`:
- `gemini_oauth_plus.py` — test Gemini with API key or Desktop OAuth.
  - API key:
    - `pip install google-generativeai`
    - `export GOOGLE_API_KEY=...`
    - `python gemini_oauth_plus.py --model gemini-2.0-flash`
  - OAuth:
    - `pip install google-auth-oauthlib google-generativeai`
    - Create OAuth 2.0 client (Desktop) in GCP; download `client_secret.json` into that folder
    - `python gemini_oauth_plus.py --oauth --model gemini-2.0-flash`

## Gemini CLI (Official Open‑Source) — Research Notes & Links

- Project repos and docs (official):
  - GitHub: https://github.com/google-gemini/gemini-cli
  - Google Cloud docs (Gemini for Google Cloud): https://cloud.google.com/gemini/docs/codeassist/gemini-cli
  - Google blog (announcement): https://blog.google/technology/developers/introducing-gemini-cli-open-source-ai-agent/
  - Commands reference: https://github.com/google-gemini/gemini-cli/blob/main/docs/cli/commands.md
  - Codelab: https://codelabs.developers.google.com/gemini-cli-hands-on
- Install (as published in repo):
  - `npm install -g @google/gemini-cli@nightly` (subject to change as releases stabilize)
- Auth & keys:
  - The CLI supports personal account access to Gemini 2.5 Pro (per blog) and can use Google AI Studio or Vertex AI keys.
  - For API‑key path in ActCLI today, use `GOOGLE_API_KEY` with our native adapter; for CLI‑backed experiments, see below.
- ActCLI experimentation:
  - We provide an experimental shim at `experiments/cli-playground/gemini_cli_shim.py` which uses `GOOGLE_API_KEY` if present (or stubs output).
  - We can add a GeminiCLIAdapter when the CLI stabilizes; for now, use the shim for demos or stick with the API adapter for production.


## Notes & Safety

- Cloud is disabled by default; turn on in REPL with `/share cloud on`.
- API keys are read from env only; vendor CLIs manage their own login states.
- CLI-backed adapters treat “model” as a label; execution uses the active CLI selection.

## Troubleshooting

- Providers readiness: `actcli providers doctor`
- Codex/Claude issues: re-run vendor CLI to re-auth, or `actcli providers login <cli>`
- Gemini 403: ensure the Generative Language API is enabled; set `GOOGLE_CLOUD_PROJECT` if needed.
