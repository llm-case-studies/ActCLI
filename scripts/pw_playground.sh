#!/usr/bin/env bash
set -euo pipefail

# Runs the Playwright Playground E2E suite against the extension’s local test pages.
# - Starts a local static server on port 4400
# - Installs Chromium for PW if needed
# - Runs all E2E specs (OSS tests are gated and will be skipped)

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXT_DIR="$ROOT_DIR/extensions/generic-chat-bridge"
E2E_DIR="$EXT_DIR/tests/e2e"

if [[ ! -d "$EXT_DIR" ]]; then
  echo "Extension directory not found: $EXT_DIR" >&2
  exit 1
fi

pushd "$EXT_DIR" >/dev/null

echo "[PW] Starting local server: http://127.0.0.1:4400"
python3 -m http.server 4400 >/dev/null 2>&1 &
SRV_PID=$!
cleanup() { kill "$SRV_PID" 2>/dev/null || true; }
trap cleanup EXIT

echo "[PW] Installing Chromium (if needed)…"
npx playwright install chromium >/dev/null

echo "[PW] Running E2E suite (Playground)…"
pushd "$E2E_DIR" >/dev/null
EXTENSION_PATH="$EXT_DIR" npx playwright test -c playwright.config.ts
STATUS=$?
popd >/dev/null

exit $STATUS

