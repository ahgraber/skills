#!/usr/bin/env bash
# Logging Template (Bash)

timestamp() {
  date '+%Y-%m-%dT%H:%M:%S%z'
}

log() {
  local level=$1
  shift
  local ts
  ts="$(timestamp)"
  printf '%s [%s] %s\n' "${ts}" "${level}" "$*" >&2
}

log_debug() { [[ "${DEBUG:-0}" == "1" ]] && log "DEBUG" "$*"; }
log_info()  { log "INFO" "$*"; }
log_warn()  { log "WARN" "$*"; }
log_error() { log "ERROR" "$*"; }

die() {
  log_error "$*"
  exit 1
}
