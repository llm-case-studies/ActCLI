#!/usr/bin/env bash
set -euo pipefail

# Fresh runner: stops project-local Ollama server on 11435, starts a new one,
# waits until healthy, then executes the requested actcli command against it.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/models"
HOST="127.0.0.1:11435"
BASE_URL="http://$HOST"
PID_FILE="$MODELS_DIR/ollama-serve.pid"
LOG_FILE="$MODELS_DIR/ollama-serve.log"

kill_port() {
  local port=$1
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -ti tcp:"$port" || true)
    if [[ -n "$pids" ]]; then
      echo "Killing PIDs on port $port: $pids"
      kill $pids || true
    fi
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "$port"/tcp || true
  else
    echo "No lsof/fuser; cannot proactively free port $port" >&2
  fi
}

start_server_bg() {
  mkdir -p "$MODELS_DIR"
  echo "Starting Ollama @ $HOST (models in $MODELS_DIR)"
  # shellcheck disable=SC2086
  OLLAMA_MODELS="$MODELS_DIR" OLLAMA_HOST="$HOST" nohup ollama serve >"$LOG_FILE" 2>&1 &
  echo $! >"$PID_FILE" || true
}

wait_ready() {
  echo -n "Waiting for Ollama to become ready"
  for i in {1..60}; do
    if curl -sS "$BASE_URL/api/tags" >/dev/null 2>&1; then
      echo " — ready"
      return 0
    fi
    echo -n "."
    sleep 1
  done
  echo
  echo "Server did not become ready; see $LOG_FILE" >&2
  exit 1
}

inject_host_arg() {
  # If --ollama-host is already present, leave args unchanged
  for a in "$@"; do
    if [[ "$a" == --ollama-host* ]]; then
      printf '%s\n' "$@"
      return 0
    fi
  done
  printf '%s\n' "$@" --ollama-host "$BASE_URL"
}

usage() {
  cat <<EOF
Usage: scripts/fresh.sh <subcommand> [args]

Subcommands (run after fresh server start):
  chat [--prompt ... --multi ...]   Run actcli chat against the fresh server
  models list                        List models on the fresh server
  models pull [--all|--models ...]   Pull models (streams progress)
  pull-all                           Shortcut for: models pull --all
  reset                              Only reset server (stop + start + wait)

Examples:
  scripts/fresh.sh pull-all
  scripts/fresh.sh chat --prompt "Compare approaches" --multi "codellama:34b,gpt-oss:20b"
  scripts/fresh.sh models list
EOF
}

if [[ $# -lt 1 ]]; then
  usage; exit 2
fi

cmd=$1; shift || true

echo "Stopping any project-local Ollama on $HOST (if present)"
kill_port 11435 || true

start_server_bg
wait_ready

case "$cmd" in
  reset)
    echo "Fresh server is up at $BASE_URL"
    ;;
  pull-all)
    # Shortcut for: models pull --all
    args=("$(inject_host_arg actcli models pull --all "$@")")
    # shellcheck disable=SC2046
    eval ${args[@]}
    ;;
  chat)
    args=("$(inject_host_arg actcli chat "$@")")
    # shellcheck disable=SC2046
    eval ${args[@]}
    ;;
  models)
    args=("$(inject_host_arg actcli models "$@")")
    # shellcheck disable=SC2046
    eval ${args[@]}
    ;;
  *)
    echo "Unknown subcommand: $cmd" >&2
    usage
    exit 2
    ;;
esac
