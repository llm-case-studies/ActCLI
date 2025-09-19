# MCP Setup (Local Folders)

This project supports running MCP servers locally and registering them with ActCLI. For easy sharing with clients and to keep the repo lean, place MCPs under a project folder and ignore them in git.

## Folder Layout (recommended)
- `available-mcp/`               # MCP servers copied here (ignored by git)
  - `memory/`                    # e.g., Memory-MCP
    - `README.md`
    - `run.sh`                   # starts the server (HTTP or stdio wrapper)
    - `server.json`              # metadata: name, port/url, command
  - `prior-self/`
    - `README.md`
    - `run.sh`
    - `server.json`

Git ignore: `available-mcp/` is ignored by default. Share this folder out-of-band when needed.

## Registering MCPs with ActCLI
- Start the server (example): `available-mcp/memory/run.sh`
- Add to ActCLI:
  - `actcli mcp add memory http://127.0.0.1:9010 --group memory --desc "Memory MCP"`
  - `actcli mcp on memory`
  - Optional logging: `actcli mcp log memory --enable true`
- Test reachability:
  - `actcli mcp test memory` (HTTP health/HEAD)

Tip: you can keep a project config at `.actcli/mcp.toml` with servers you use often.

## Deep Tests (Optional)
Some servers expose a health tool; if not, define a "deep test" in your docs/run script. We will extend `actcli mcp test` to call a configured tool (e.g., `memory.ping`).

## Security & Policy
- ActCLI honors policy: with `cloud_share=false`, remote MCPs are disabled.
- Enable per-server logging only when you want request/response logs in `out/mcp-logs/`.

## Quick Script Template (`run.sh`)
```
#!/usr/bin/env bash
set -euo pipefail
PORT=${PORT:-9010}
echo "Starting Memory-MCP on :$PORT"
# Example HTTP server; replace with your start command
uvx memory-mcp --port "$PORT"
```

