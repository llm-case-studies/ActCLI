#!/usr/bin/env bash
set -euo pipefail

# Project-local Ollama helper
# - Serves Ollama on a dedicated port with models stored under ./models
# - Pulls a default set of models for this project

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MODELS_DIR="$ROOT_DIR/models"
HOST="127.0.0.1:11435"
BASE_URL="http://$HOST"

DEFAULT_MODELS=(
  "codellama:34b"
  "gpt-oss:20b"
  "codellama:13b"
  "llama3:8b"
  "llama3.2:3b"
)

usage() {
  cat <<EOF
Usage: scripts/ollama-local.sh <command>

Commands:
  serve            Start Ollama server on $HOST with models in ./models
  pull-all         Pull default models into the project store
  pull <tags...>   Pull specific tags (e.g., codellama:34b llama3:8b)
  status           Show models on the project server

Tips:
  export OLLAMA_HOST=$BASE_URL to target this server in actcli.
  Or pass --ollama-host $BASE_URL to actcli commands.
EOF
}

cmd=${1:-}
case "$cmd" in
  serve)
    mkdir -p "$MODELS_DIR"
    echo "Serving Ollama at $HOST with models dir $MODELS_DIR"
    OLLAMA_MODELS="$MODELS_DIR" OLLAMA_HOST="$HOST" ollama serve
    ;;
  pull-all)
    shift || true
    for tag in "${DEFAULT_MODELS[@]}"; do
      echo "Pulling $tag → $BASE_URL"
      OLLAMA_HOST="$BASE_URL" ollama pull "$tag"
    done
    ;;
  pull)
    shift || true
    if [ "$#" -eq 0 ]; then
      echo "No tags provided" >&2
      exit 2
    fi
    for tag in "$@"; do
      echo "Pulling $tag → $BASE_URL"
      OLLAMA_HOST="$BASE_URL" ollama pull "$tag"
    done
    ;;
  status)
    curl -s "$BASE_URL/api/tags" || true
    ;;
  *)
    usage
    exit 2
    ;;
esac

