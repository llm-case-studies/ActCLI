#!/usr/bin/env bash
set -euo pipefail

# Runs the Rocket.Chat UI E2E test.
# Usage examples:
#   scripts/pw_rocketchat.sh                 # reuse profile state
#   PW_FRESH=1 scripts/pw_rocketchat.sh      # force clean profile (no cached login)

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXT_DIR="$ROOT_DIR/extensions/generic-chat-bridge"
E2E_DIR="$EXT_DIR/tests/e2e"

if [[ ! -d "$EXT_DIR" ]]; then
  echo "Extension directory not found: $EXT_DIR" >&2
  exit 1
fi

pushd "$EXT_DIR" >/dev/null

echo "[PW] Installing Chromium (if needed)…"
npx playwright install chromium >/dev/null

echo "[PW] Running Rocket.Chat UI test…"
pushd "$E2E_DIR" >/dev/null
EXTENSION_PATH="$EXT_DIR" RUN_OSS=1 ${PW_FRESH:+PW_FRESH=$PW_FRESH} \
  npx playwright test -c playwright.config.ts rocketchat-ui.spec.ts
STATUS=$?
popd >/dev/null

exit $STATUS

