#!/usr/bin/env bash
set -euo pipefail

# ActCLI • Playground server helper
#
# Commands:
#   start [--port N]      Kill any server on the port, then start a new one (default port 4400)
#   start:parallel        Start a new server on a free port (auto-picks); prints URL
#   stop  [--port N|all]  Stop the server on the port (or all known pidfiles)
#   status                Show running servers started via this script
#
# Servers are rooted at: extensions/generic-chat-bridge/
# We write pidfiles/logs next to that folder (hidden files).

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
EXT_DIR="$ROOT_DIR/extensions/generic-chat-bridge"
PID_DIR="$EXT_DIR/.pg"
mkdir -p "$PID_DIR"

port=4400
cmd="${1:-start}"
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    -p|--port) port=${2:?}; shift 2;;
    *) echo "Unknown arg: $1" >&2; exit 2;;
  esac
done

is_port_free() {
  local p=$1
  if command -v lsof >/dev/null 2>&1; then
    ! lsof -iTCP:"$p" -sTCP:LISTEN >/dev/null 2>&1
  elif command -v ss >/dev/null 2>&1; then
    ! ss -ltn "sport = :$p" | grep -q ":$p"
  else
    # best-effort
    ! (echo >/dev/tcp/127.0.0.1/$p) >/dev/null 2>&1
  fi
}

kill_on_port() {
  local p=$1
  # kill any process listening on the port (best-effort)
  if command -v lsof >/dev/null 2>&1; then
    local pids
    pids=$(lsof -t -iTCP:"$p" -sTCP:LISTEN || true)
    [[ -n "$pids" ]] && kill $pids 2>/dev/null || true
  elif command -v fuser >/dev/null 2>&1; then
    fuser -k "$p"/tcp 2>/dev/null || true
  else
    pkill -f "http\.server $p" 2>/dev/null || true
  fi
  # kill pidfile if present
  local pf="$PID_DIR/server-$p.pid"
  if [[ -f "$pf" ]]; then
    local pid
    pid=$(cat "$pf" || true)
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
    rm -f "$pf"
  fi
}

pick_free_port() {
  python3 - "$@" <<'PY'
import socket
s=socket.socket(); s.bind(("127.0.0.1",0))
print(s.getsockname()[1])
s.close()
PY
}

start_server() {
  local p=$1
  local log="$PID_DIR/server-$p.log"
  pushd "$EXT_DIR" >/dev/null
  echo "[playground] starting http://127.0.0.1:$p (root=$EXT_DIR)"
  # Bind explicitly to loopback
  python3 -m http.server "$p" --bind 127.0.0.1 >"$log" 2>&1 &
  local pid=$!
  echo $pid > "$PID_DIR/server-$p.pid"
  popd >/dev/null
  echo "PID=$pid • Log=$log"
}

case "$cmd" in
  start)
    kill_on_port "$port"
    start_server "$port"
    ;;
  start:parallel)
    if ! is_port_free "$port"; then
      port=$(pick_free_port)
    fi
    start_server "$port"
    ;;
  stop)
    if [[ "$port" == "all" ]]; then
      for pf in "$PID_DIR"/server-*.pid; do
        [[ -f "$pf" ]] || continue
        kill "$(cat "$pf")" 2>/dev/null || true
        rm -f "$pf"
      done
    else
      kill_on_port "$port"
    fi
    echo "[playground] stopped"
    ;;
  status)
    echo "[playground] servers:"
    for pf in "$PID_DIR"/server-*.pid; do
      [[ -f "$pf" ]] || continue
      p="${pf##*-}"; p="${p%.pid}"
      pid=$(cat "$pf" || true)
      if [[ -n "$pid" && -d "/proc/$pid" ]]; then
        echo "  - http://127.0.0.1:$p (pid=$pid)"
      else
        echo "  - stale pidfile for port $p" && rm -f "$pf"
      fi
    done
    ;;
  *)
    cat << EOF
Usage: $0 <start|start:parallel|stop|status> [--port N]
Examples:
  $0 start                 # kill previous on 4400 and start new
  $0 start --port 4410     # kill previous on 4410 and start new
  $0 start:parallel        # start new on a free port (keeps others running)
  $0 stop --port 4400      # stop server on 4400
  $0 stop --port all       # stop all servers started via this script
  $0 status                # list running servers
EOF
    ;;
esac

