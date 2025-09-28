#!/usr/bin/env bash
set -euo pipefail

# Rocket.Chat manager wrapper
#
# Subcommands:
#   up       - docker compose up -d in extensions/generic-chat-bridge/docker
#   down     - docker compose down
#   status   - docker compose ps
#   logs     - docker compose logs -f rocketchat
#   seed     - run scripts/seed_rocketchat.sh
#
# Usage examples:
#   bash scripts/rc.sh up
#   bash scripts/rc.sh seed
#   bash scripts/rc.sh status

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_DIR="$ROOT_DIR/extensions/generic-chat-bridge/docker"

if [[ ! -d "$DOCKER_DIR" ]]; then
  echo "Docker directory not found: $DOCKER_DIR" >&2
  exit 1
fi

cmd=${1:-help}
shift || true

case "$cmd" in
  up)
    pushd "$DOCKER_DIR" >/dev/null
    echo "[rc] docker compose up -d"
    docker compose up -d
    popd >/dev/null
    ;;
  down)
    pushd "$DOCKER_DIR" >/dev/null
    echo "[rc] docker compose down"
    docker compose down
    popd >/dev/null
    ;;
  status)
    pushd "$DOCKER_DIR" >/dev/null
    docker compose ps
    popd >/dev/null
    ;;
  logs)
    pushd "$DOCKER_DIR" >/dev/null
    docker compose logs -f rocketchat
    popd >/dev/null
    ;;
  seed)
    bash "$ROOT_DIR/scripts/seed_rocketchat.sh"
    ;;
  help|*)
    cat << EOF
Usage: $0 <up|down|status|logs|seed>

Subcommands:
  up       Start Rocket.Chat stack via docker compose
  down     Stop Rocket.Chat stack
  status   Show docker compose services status
  logs     Tail Rocket.Chat service logs
  seed     Seed users/channel (delegates to scripts/seed_rocketchat.sh)
EOF
    ;;
esac

