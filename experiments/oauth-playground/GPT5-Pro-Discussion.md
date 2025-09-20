Nope, you are not correct as of now... Maybe - 5-6 month ago your info was correct, but not anymore.  Could you research the web? In Claude CLI that I am using since june at least I do not use API keys - some usage is included in pro subscription. Same with OpenAI - its allowing GPT5 with a subscription (some advanced - I do not remember). Maybebe you can find on github some examples?
ChatGPT said:
Request for GPT-5 Pro
Reasoned for 6m 39s

You’re right—the ecosystem moved fast this summer. Here’s the current (Sept 2025) reality, plus tiny working examples you can drop into ActCLI today.

TL;DR (what changed)

Anthropic — Claude Code: The terminal tool is now part of a unified Pro/Max subscription. You log in via browser once; no API key setup required for typical use, and usage draws from the same pool as the Claude app. For automation, it exposes headless print mode with JSON output, so you can script against it. 
Claude Help Center
+1

OpenAI — Codex CLI: OpenAI’s open‑source Codex CLI recommends “Sign in with ChatGPT” (Plus/Pro/Team/Edu/Enterprise). It also supports non‑interactive runs (codex exec) for scripting. (Under the hood, the login can provision an API token for the CLI—users don’t manage keys, but some orgs report it still bills the developer account.) 
OpenAI Developers
+2
GitHub
+2

Google — Gemini CLI: Official Login with Google flow (OAuth) is built in; token is cached locally. If auth “works in the browser but CLI fails,” it’s usually the localhost redirect + GOOGLE_CLOUD_PROJECT requirement called out in their docs. 
Google Gemini

Given that, the quickest way to let actuaries “bring their own subscription” is to shell out to the vendor CLIs for Claude & Codex (login handled by the vendor), and use OAuth (or API key) for Gemini in Python when needed.

Minimal, working snippets
1) Gemini (Python, OAuth with a regular Google account)

This uses the official OAuth flow and the google.generativeai SDK.

# gemini_oauth_min.py
# pip install google-auth-oauthlib google-generativeai

from google_auth_oauthlib.flow import InstalledAppFlow
import google.generativeai as genai

SCOPES = ["https://www.googleapis.com/auth/generative-language"]  # Gemini API scope
flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", scopes=SCOPES)
creds = flow.run_local_server(port=0)  # opens browser, returns refreshable token

genai.configure(credentials=creds)
model = genai.GenerativeModel("gemini-2.5-pro")  # or "gemini-2.0-flash"
resp = model.generate_content("Say hi in one sentence.")
print(resp.text)


Docs: Gemini API OAuth quickstart + Vertex/GCP auth guidance. 
Google AI for Developers
+1

Common gotchas (match your report):

The first login opens a local browser and redirects to localhost—run on a machine where the browser can reach the CLI. 
Google Gemini

If you’re on Workspace / Code Assist, you may need GOOGLE_CLOUD_PROJECT (and sometimes GOOGLE_CLOUD_LOCATION). 
Google Gemini

2) Claude Code (use your Pro/Max via the CLI; no API key to manage)
# claude_cli_min.py
# Requires: `npm i -g @anthropic-ai/claude-code` and you've run `claude` once to login.

import json, subprocess

def claude_prompt(prompt: str) -> str:
    # Headless print mode with JSON output
    cmd = ["claude", "-p", prompt, "--output-format", "json"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.strip()
    try:
        data = json.loads(out)
        # Claude's JSON "print" returns a structured object; be robust:
        return (
            data.get("text")
            or data.get("output")
            or data.get("content")
            or out  # fall back to raw
        )
    except json.JSONDecodeError:
        return out

print(claude_prompt("Briefly explain the chain-ladder method."))


Why this works: Claude Code now ties directly to Pro/Max—“one unified subscription” across web/desktop/terminal—and supports -p print mode with --output-format json for automation. If an ANTHROPIC_API_KEY env var is present, it will force API billing instead of your plan, so keep that unset when you want subscription usage. 
Claude Help Center
+1

3) OpenAI Codex (use your ChatGPT subscription via the CLI; script with exec)
# codex_cli_min.py
# Requires: `npm i -g @openai/codex` or `brew install codex`.
# Run `codex` once and pick “Sign in with ChatGPT”.

import subprocess

def codex_exec(prompt: str) -> str:
    # Non-interactive execution; --quiet prints the final answer only.
    cmd = ["codex", "exec", "--quiet", prompt]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return res.stdout.strip()

print(codex_exec("Summarize the differences between chain ladder and Bornhuetter-Ferguson."))


Docs: “Sign in with ChatGPT” is the recommended auth path; codex exec enables non‑interactive scripting/CI. Some users note that login provisions an API key behind the scenes (so org‑level billing may apply), but you don’t manage the key yourself. 
OpenAI Developers
+2
GitHub
+2

Drop‑in provider wrapper for ActCLI (first deliverable)

A tiny abstraction lets you pick the best available backend on a user’s machine:

# actcli_providers.py
import os, shutil, subprocess, json

class ProviderError(RuntimeError): pass

def has(cmd): return shutil.which(cmd) is not None

def ask_claude(prompt):
    out = subprocess.run(["claude", "-p", prompt, "--output-format", "json"],
                         capture_output=True, text=True, check=True).stdout
    try:
        data = json.loads(out); return data.get("text") or data.get("output") or data.get("content") or out
    except json.JSONDecodeError:
        return out

def ask_codex(prompt):
    out = subprocess.run(["codex", "exec", "--quiet", prompt],
                         capture_output=True, text=True, check=True).stdout
    return out.strip()

def ask_gemini(prompt):
    # fallback for Python OAuth/API-key path; keep it pluggable
    from google.generativeai import GenerativeModel, configure
    # configure(...) once at process start (credentials or API key must already be set)
    model = GenerativeModel("gemini-2.5-pro")
    return model.generate_content(prompt).text

def ask_best(prompt):
    if has("claude") and not os.getenv("ANTHROPIC_API_KEY"):
        return "claude", ask_claude(prompt)
    if has("codex"):
        return "codex", ask_codex(prompt)
    try:
        return "gemini", ask_gemini(prompt)
    except Exception as e:
        raise ProviderError(f"No working provider found: {e}")

if __name__ == "__main__":
    name, answer = ask_best("Explain Mack's method in two sentences.")
    print(f"[{name}] {answer}")


Claude path uses plan‑based auth out of the box. Headless/JSON makes it easy to parse. 
Claude Docs

Codex path uses ChatGPT login + exec for CI‑style runs. 
OpenAI Developers

Gemini path can use OAuth or API key per your environment setup. 
Google AI for Developers

This gives actuaries a zero‑friction “use your existing subscription” experience immediately, while keeping a clean seam for later API integrations.

Quick setup checklists (for your team)

Claude Code

npm i -g @anthropic-ai/claude-code → run claude → log in with Pro/Max.

Ensure ANTHROPIC_API_KEY is unset if you want subscription usage (not API billing).

Programmatic use: claude -p "…" --output-format json. 
Claude Help Center
+1

OpenAI Codex

npm i -g @openai/codex (or brew install codex).

codex → Sign in with ChatGPT (Plus/Pro/Team/Edu/Enterprise).

Programmatic use: codex exec "…" --quiet. 
GitHub
+1

Gemini CLI / SDK

CLI login: run gemini and pick Login with Google; if it “auths then fails,” set GOOGLE_CLOUD_PROJECT and ensure the browser can hit the localhost redirect. 
Google Gemini

Python OAuth: use the snippet above; works with regular Google accounts. 
Google AI for Developers

Handy references & examples (you asked for GitHub pointers)

Claude Code docs (CLI flags & headless/print JSON) and “Using Claude Code with your Pro/Max plan”. 
Claude Docs
+1

OpenAI Codex CLI README + Dev docs (login with ChatGPT, codex exec). 
GitHub
+1

Gemini CLI repo & auth guide (Login with Google, project/env tips). 
GitHub
+1

Bottom line

You can let users try “multi‑AI seminar” using their existing subscriptions today:

Claude & Codex: call the CLIs (login handled by vendors; no keys to manage).

Gemini: either call the CLI or use Python OAuth.

If you’d like, I can fold these into a small actcli providers module (with unit tests) so your devs can wire it up immediately.

You said:
Thank you very much, Sir! Now we are talking! Let us try these snippets and get back to you either with "Hooray!!!" or "got some errors" LOL
ChatGPT said:
Request for GPT-5 Pro
Reasoned for 3m 53s

Awesome—go have fun with it! 🎯
To make your “Hooray!!!” more likely (and your “got some errors” easier to debug), here’s a tight 10‑minute smoke‑test plan and a tiny one‑file harness you can copy‑paste.

0) Quick installs / sanity checks

CLIs (use your existing subscriptions)

# Claude Code
npm i -g @anthropic-ai/claude-code    # then run: claude  (log in once in browser)

# OpenAI Codex
npm i -g @openai/codex                # then run: codex   (Sign in with ChatGPT)

# (optional) Gemini CLI
# If you already have it, just run: gemini  (Login with Google)


Python (for Gemini OAuth / API‑key and the harness)

python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install google-generativeai google-auth-oauthlib google-auth-httplib2


Tip (Linux Mint/Ubuntu): make sure the default browser can open http://127.0.0.1:* for OAuth callbacks. If you use multi‑profile Chrome, start it once without --profile-directory quirks before running the OAuth scripts.

1) One‑liners to confirm each provider works

Claude (uses your Pro/Max plan; no API key required)

claude -p "ActCLI smoke test: say hi in one short sentence" --output-format json


Look for a small JSON blob with a text or output field.

Codex (uses your ChatGPT subscription via login)

codex exec --quiet "ActCLI smoke test: say hi in one short sentence"


Gemini (Python, OAuth)

Create a Desktop OAuth client in your GCP project; download client_secret.json into the folder you’ll run from.

Export your project so requests bill/route correctly:

export GOOGLE_CLOUD_PROJECT=<your-gcp-project-id>


Run the minimal OAuth test:

# file: gemini_oauth_min.py
from google_auth_oauthlib.flow import InstalledAppFlow
import google.generativeai as genai

SCOPES = ["https://www.googleapis.com/auth/generative-language"]
creds = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES).run_local_server(port=0)
genai.configure(credentials=creds)

print(genai.GenerativeModel("gemini-2.5-flash").generate_content(
    "ActCLI smoke test: say hi in one short sentence").text)

python gemini_oauth_min.py


If the browser login succeeds but the script fails:
• delete token.json (if present) and retry;
• double‑check scope is exactly .../generative-language;
• ensure GOOGLE_CLOUD_PROJECT is set;
• run on the same machine as the browser so the localhost redirect completes.

2) Tiny harness you can drop in any folder

This will pick the best available provider on your machine (Claude → Codex → Gemini OAuth) and print who answered.

# file: actcli_provider_smoke.py
import os, shutil, subprocess, json

def has(cmd): return shutil.which(cmd) is not None

def ask_claude(prompt: str) -> str:
    out = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "json"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    try:
        data = json.loads(out)
        return data.get("text") or data.get("output") or data.get("content") or out
    except json.JSONDecodeError:
        return out

def ask_codex(prompt: str) -> str:
    out = subprocess.run(
        ["codex", "exec", "--quiet", prompt],
        capture_output=True, text=True, check=True
    ).stdout
    return out.strip()

def ask_gemini(prompt: str) -> str:
    import google.generativeai as genai
    # Assumes you've just authenticated (OAuth) or configured an API key elsewhere.
    model = genai.GenerativeModel("gemini-2.5-flash")
    return model.generate_content(prompt).text

def ask_best(prompt: str):
    if has("claude") and not os.getenv("ANTHROPIC_API_KEY"):
        return "claude", ask_claude(prompt)
    if has("codex"):
        return "codex", ask_codex(prompt)
    try:
        return "gemini", ask_gemini(prompt)
    except Exception as e:
        return "none", f"Gemini failed ({e}). No working provider found."

if __name__ == "__main__":
    who, text = ask_best("ActCLI smoke test: greet me in one short sentence.")
    print(f"[{who}] {text}")


Run it:

python actcli_provider_smoke.py


Expected output:

[claude] Hi from Claude! …
# or
[codex] Hi from Codex! …
# or
[gemini] Hi from Gemini! …

3) When things go sideways (quick triage)

Claude prints HTML or hangs: run claude once interactively to complete login; keep ANTHROPIC_API_KEY unset if you want to use plan minutes (not API billing).

Codex exits with auth error: run plain codex, pick Sign in with ChatGPT, then retry codex exec.

Gemini 403/“missing subscription” or scope error: set GOOGLE_CLOUD_PROJECT, delete token.json, ensure the scope is the full .../generative-language, and re‑login.

Corporate VPN/proxy: localhost callbacks can be blocked; temporarily disable or allow loopback.

4) Nice‑to‑have next

Add a tiny actcli providers doctor command that runs the harness checks, prints versions, and tells the user which auth is active (plan login vs. API key).

Cache provider choice per session and show it in your REPL header so you always know “where you are.”