# Git-MCP Requirements (Minimal, Safe, Consistent)

## Purpose & Scope
A small, ToS-friendly MCP tool exposing the essential Git operations ActCLI needs for local repos and simple PR preparation. Optimized for safety, reproducibility, and consistent behavior across agents (ActCLI, Claude, Gemini). No destructive commands by default; no direct PR creation via API unless explicitly enabled.

## Capabilities (Tools)
- repo_detect → Detect repo context
  - Returns: is_repo, root, branch, default_branch, remotes[] (name,url), clean(bool)
- repo_init → Initialize repo
  - Params: default_branch? ("main"), user_name?, user_email?
- status → Porcelain status
  - Returns: branch, ahead, behind, staged[], changed[], untracked[]
- add → Stage paths
  - Params: paths[] (globs supported), update?(bool=false)
- commit → Create commit
  - Params: message, signoff?(bool), amend?(bool=false), allow_empty?(bool=false)
  - Returns: hash
- branch_current | branch_create | branch_switch
  - Params (create/switch): name
- remote_add | remote_set
  - Params: name (e.g., "origin"), url
- fetch | pull | push
  - fetch: remote? (default origin)
  - pull: remote? (default origin), rebase?(false), ff_only?(true)
  - push: remote? (origin), branch? (current), set_upstream?(true), force?(false)
- log → Last N commits
  - Params: limit(int=10)
  - Returns: [{hash, subject, author, date}]
- diff → Unified diff
  - Params: base?(default: HEAD), head?(default: working), paths?[]
  - Returns: unified_text
- tag_create → Lightweight/annotated tag
  - Params: name, message? (annotated when provided)
- ensure_gitignore → Idempotent additions
  - Params: entries[] (e.g., ["models/", ".venv/", "__pycache__/," "out/"])
- pr_link → Construct web PR URL (no API)
  - Params: remote?(origin), target?(default_branch), branch?(current), host?(auto-detect)
  - Returns: url

## Safety & Policy (Defaults)
- No destructive ops: no force push, no reset, no clean.
- pull: fast-forward only unless rebase=true.
- push: requires upstream or set_upstream=true; no force.
- Path scoping: reject paths that traverse outside repo root.
- Network/timeouts: short connect timeout; clear errors when remotes unreachable.

## Standard PR Flow (Uniform Across Agents)
1) repo_detect → ensure repo and default_branch
2) branch_create (or switch) → `feat/<slug>` (or `fix/`, `chore/`)
3) add → explicit globs (no implicit `.`)
4) commit → Conventional Commit (first line = PR title)
5) push → `--set-upstream` to remote (origin)
6) pr_link → print web URL for manual PR creation (no API calls)
   - GitHub: `https://github.com/<org>/<repo>/compare/<target>...<branch>?expand=1&title=...&body=...`
   - GitLab: `https://gitlab.com/<ns>/<repo>/-/merge_requests/new?merge_request[source_branch]=<branch>&merge_request[target_branch]=<target>&merge_request[title]=...`
   - Gitea: `https://<host>/<ns>/<repo>/compare/<target>...<branch>?title=...&body=...`

## Request/Response Shape (All Tools)
- Request: `{ "op": "add", "params": { ... } }`
- Response: `{ "ok": true, "data": { ... }, "exit_code": 0 }` on success
- Errors: `{ "ok": false, "error": { "type": "validation|exec|env", "message": "..." }, "exit_code": <int> }`

### Selected Schemas (abridged)
- repo_detect → data: `{ is_repo, root, branch, default_branch, remotes: [{name,url}], clean }`
- status → data: `{ branch, ahead, behind, staged:[{path}], changed:[{path}], untracked:[{path}] }`
- commit → data: `{ hash }`
- pr_link → data: `{ url }`

## Host Detection & PR URL Rules
- Determine host from `remote.origin.url`:
  - GitHub SSH/HTTPS → build GitHub compare URL
  - GitLab → new MR URL as above
  - Gitea → compare URL
- Default target = remote default branch if discoverable; else `main`.
- URL-encode title/body; include commit subject as title and subsequent lines as body when available.

## Configuration & Env
- `GIT_SSH_COMMAND`, `SSH_AUTH_SOCK` respected when present.
- Optional: `ACTCLI_PR_REMOTE` (defaults to `origin`).
- Optional: `ACTCLI_DEFAULT_BRANCH` override.

## Error Handling
- Clear, actionable messages: missing remote, detached HEAD, diverged branch, auth denied.
- No retries on push/pull by default; return error + suggestion.
- Validation errors for bad params (e.g., empty paths on add).

## Non-Goals (v1)
- No force operations, no rebase/merge helpers beyond pull(rebase)/fast-forward.
- No API-based PR creation by default (can be a separate opt-in tool).
- No stash/clean/reset; can be future tools with explicit confirmation.

## ActCLI Integration (Examples)
- `actcli pr prepare -m "feat(chat): add REPL" --files "src/**,README.md" --branch feat/chat-repl --target main`
  → repo_detect → branch_create → add → commit → push → pr_link
- REPL: `/pr prepare -m "fix: adapter timeout" --files "src/actcli/seminar/**"`
  → prints clickable PR URL; user confirms in browser.

