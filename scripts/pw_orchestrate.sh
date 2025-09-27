#!/usr/bin/env bash
set -euo pipefail

# Orchestrates common E2E flows in one place.
# Subcommands:
#   env:playground       — start local server for playground (port 4400)
#   env:rc               — ensure Rocket.Chat docker is up (delegated to docker compose)
#   seed:rc              — seed Rocket.Chat users/channel (uses docker/.env)
#   test:playground      — run all local E2E
#   test:rc              — run Rocket.Chat UI E2E (respects PW_FRESH, RC_LOGIN_MODE)

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

cmd=${1:-help}
shift || true

case "$cmd" in
  env:playground)
    pushd "$ROOT_DIR/extensions/generic-chat-bridge" >/dev/null
    echo "[env] playground → http://127.0.0.1:4400"
    python3 -m http.server 4400
    ;;
  env:rc)
    pushd "$ROOT_DIR/extensions/generic-chat-bridge/docker" >/dev/null
    echo "[env] docker compose up -d (Rocket.Chat + deps)"
    docker compose up -d
    ;;
  seed:rc)
    bash "$ROOT_DIR/scripts/seed_rocketchat.sh"
    ;;
  test:playground)
    bash "$ROOT_DIR/scripts/pw_playground.sh"
    ;;
  test:rc)
    bash "$ROOT_DIR/scripts/pw_rocketchat.sh"
    ;;
  help|*)
    cat << EOF
Usage: $0 <command>

Commands:
  env:playground   Start local server for playground (http://127.0.0.1:4400)
  env:rc           Bring up Rocket.Chat via docker compose
  seed:rc          Seed users/channel in Rocket.Chat (reads docker/.env)
  test:playground  Run local Playwright E2E suite
  test:rc          Run Rocket.Chat UI E2E (PW_FRESH=1 for clean login; RC_LOGIN_MODE api|ui|api-first)

Examples:
  $0 env:rc && $0 seed:rc
  PW_FRESH=1 RC_LOGIN_MODE=api-first $0 test:rc
  $0 test:playground
EOF
    ;;
esac

