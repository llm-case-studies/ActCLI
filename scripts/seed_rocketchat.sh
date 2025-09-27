#!/usr/bin/env bash
set -euo pipefail

# Seeds Rocket.Chat with users and channel using the docker/.env configuration.
# - Expects admin to be created via web wizard once
# - Reads variables from extensions/generic-chat-bridge/docker/.env if present

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DOCKER_DIR="$ROOT_DIR/extensions/generic-chat-bridge/docker"

if [[ ! -d "$DOCKER_DIR" ]]; then
  echo "Docker folder not found: $DOCKER_DIR" >&2
  exit 1
fi

pushd "$DOCKER_DIR" >/dev/null

if [[ -f .env ]]; then
  echo "[Seed] Loading .env…"
  set -a; source .env; set +a
else
  echo "[Seed] .env not found. Using current environment." >&2
fi

echo "[Seed] Seeding Rocket.Chat users and channel…"
node seed-rocketchat.mjs
STATUS=$?
popd >/dev/null

exit $STATUS

