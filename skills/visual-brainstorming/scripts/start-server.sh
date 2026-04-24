#!/usr/bin/env bash
# Start the brainstorm server and output connection info
# Usage: start-server.sh [--project-dir <path>] [--host <bind-host>] [--url-host <display-host>] [--foreground] [--background] [--owner-monitor]
#
# Starts server on a random high port, outputs JSON with URL.
# Each session gets its own directory to avoid conflicts.
#
# Options:
#   --project-dir <path>  Store session files under <path>/.brainstorm/
#                         instead of $TMPDIR. Files persist after server stops.
#   --host <bind-host>    Host/interface to bind (default: 127.0.0.1).
#                         Use 0.0.0.0 in remote/containerized environments.
#   --url-host <host>     Hostname shown in returned URL JSON.
#   --foreground          Run server in the current terminal (no backgrounding).
#   --background          Force background mode (overrides Codex auto-foreground).
#   --owner-monitor       Enable owner-process monitoring (opt-in). The server watches
#                         a resolved grandparent PID and shuts down when it exits.
#                         Only reliable when the grandparent is a stable, long-lived
#                         process across all tool-call turns. OFF by default because
#                         sandboxed tool-call environments (Claude Code, Codex, etc.)
#                         resolve the grandparent to a short-lived orchestrator that
#                         dies between turns, triggering spurious shutdowns.
#                         The 30-minute idle timeout handles cleanup in all environments.

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Parse arguments
PROJECT_DIR=""
FOREGROUND="false"
FORCE_BACKGROUND="false"
BIND_HOST="127.0.0.1"
URL_HOST=""
OWNER_MONITOR="false"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --project-dir)
      PROJECT_DIR="$2"
      shift 2
      ;;
    --host)
      BIND_HOST="$2"
      shift 2
      ;;
    --url-host)
      URL_HOST="$2"
      shift 2
      ;;
    --foreground|--no-daemon)
      FOREGROUND="true"
      shift
      ;;
    --background|--daemon)
      FORCE_BACKGROUND="true"
      shift
      ;;
    --owner-monitor)
      OWNER_MONITOR="true"
      shift
      ;;
    --no-owner-monitor)
      # Kept for backwards compatibility; no-op since monitoring is off by default.
      shift
      ;;
    *)
      echo "{\"error\": \"Unknown argument: $1\"}"
      exit 1
      ;;
  esac
done

if [[ -z "${URL_HOST}" ]]; then
  if [[ "${BIND_HOST}" == "127.0.0.1" || "${BIND_HOST}" == "localhost" ]]; then
    URL_HOST="localhost"
  else
    URL_HOST="${BIND_HOST}"
  fi
fi

# Some environments reap detached/background processes. Auto-foreground when detected.
if [[ -n "${CODEX_CI:-}" && "${FOREGROUND}" != "true" && "${FORCE_BACKGROUND}" != "true" ]]; then
  FOREGROUND="true"
fi

# Windows/Git Bash reaps nohup background processes. Auto-foreground when detected.
if [[ "${FOREGROUND}" != "true" && "${FORCE_BACKGROUND}" != "true" ]]; then
  case "${OSTYPE:-}" in
    msys*|cygwin*|mingw*) FOREGROUND="true" ;;
    *) ;;
  esac
  if [[ -n "${MSYSTEM:-}" ]]; then
    FOREGROUND="true"
  fi
fi

# Generate unique session directory
SESSION_ID="$$-$(date +%s)-${RANDOM}"

if [[ -n "${PROJECT_DIR}" ]]; then
  SESSION_DIR="${PROJECT_DIR}/.brainstorm/${SESSION_ID}"
else
  SESSION_DIR="${TMPDIR:-/tmp}/brainstorm-${SESSION_ID}"
fi

STATE_DIR="${SESSION_DIR}/state"
PID_FILE="${STATE_DIR}/server.pid"
LOG_FILE="${STATE_DIR}/server.log"

# Create fresh session directory with content and state peers
mkdir -p "${SESSION_DIR}/content" "${STATE_DIR}"

# Mark ephemeral sessions so stop-server.sh knows to delete them
if [[ -z "${PROJECT_DIR}" ]]; then
  touch "${STATE_DIR}/ephemeral"
fi

# Kill any existing server
if [[ -f "${PID_FILE}" ]]; then
  old_pid=$(cat "${PID_FILE}")
  kill "${old_pid}" 2>/dev/null || true
  rm -f "${PID_FILE}"
fi

cd "${SCRIPT_DIR}" || { echo '{"error": "Failed to cd to script dir"}'; exit 1; }

# Owner PID monitoring is off by default. In sandboxed tool-call environments
# the grandparent resolves to a short-lived orchestrator that dies between
# turns, causing spurious shutdowns. Pass --owner-monitor to opt in when the
# grandparent is known to be a stable, long-lived process.
if [[ "${OWNER_MONITOR}" == "true" ]]; then
  grandparent_pid="$(ps -o ppid= -p "${PPID}" 2>/dev/null || true)"
  OWNER_PID="$(echo "${grandparent_pid}" | tr -d ' ')"
  if [[ -z "${OWNER_PID}" || "${OWNER_PID}" == "1" ]]; then
    OWNER_PID="${PPID}"
  fi
else
  OWNER_PID=""
fi

# Foreground mode for environments that reap detached/background processes.
if [[ "${FOREGROUND}" == "true" ]]; then
  echo "$$" > "${PID_FILE}"
  env BRAINSTORM_DIR="${SESSION_DIR}" BRAINSTORM_HOST="${BIND_HOST}" BRAINSTORM_URL_HOST="${URL_HOST}" BRAINSTORM_OWNER_PID="${OWNER_PID}" node server.cjs
  exit $?
fi

# Start server, capturing output to log file
# Use nohup to survive shell exit; disown to remove from job table
nohup env BRAINSTORM_DIR="${SESSION_DIR}" BRAINSTORM_HOST="${BIND_HOST}" BRAINSTORM_URL_HOST="${URL_HOST}" BRAINSTORM_OWNER_PID="${OWNER_PID}" node server.cjs > "${LOG_FILE}" 2>&1 &
SERVER_PID=$!
disown "${SERVER_PID}" 2>/dev/null || true
echo "${SERVER_PID}" > "${PID_FILE}"

# Wait for server-started message (check log file)
for _ in {1..50}; do
  if grep -q "server-started" "${LOG_FILE}" 2>/dev/null; then
    # Verify server is still alive after a short window (catches process reapers)
    alive="true"
    for _ in {1..20}; do
      if ! kill -0 "${SERVER_PID}" 2>/dev/null; then
        alive="false"
        break
      fi
      sleep 0.1
    done
    if [[ "${alive}" != "true" ]]; then
      echo "{\"error\": \"Server started but was killed. Retry in a persistent terminal with: ${SCRIPT_DIR}/start-server.sh${PROJECT_DIR:+ --project-dir ${PROJECT_DIR}} --host ${BIND_HOST} --url-host ${URL_HOST} --foreground\"}"
      exit 1
    fi
    grep "server-started" "${LOG_FILE}" | head -1 || true
    exit 0
  fi
  sleep 0.1
done

# Timeout - server didn't start
echo '{"error": "Server failed to start within 5 seconds"}'
exit 1
