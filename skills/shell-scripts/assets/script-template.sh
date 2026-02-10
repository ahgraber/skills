#!/usr/bin/env bash
#
# Script: your-script.sh
# Summary: One-line summary of purpose.
#
# Usage:
#   your-script.sh [-h] [-v] [-n] <input>
#
# Notes:
# - Target shell: bash
# - ShellCheck: run `shellcheck -x your-script.sh`

set -o errexit
set -o nounset
set -o pipefail

SCRIPT_NAME="$(basename "$0")"
DEBUG=0
DRY_RUN=0

usage() {
  cat <<USAGE
Usage: ${SCRIPT_NAME} [-h] [-v] [-n] <input>

Options:
  -h  Show help and exit
  -v  Verbose logging
  -n  Dry run
USAGE
}

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

log_debug() { [[ "${DEBUG}" == "1" ]] && log "DEBUG" "$*"; }
log_info()  { log "INFO" "$*"; }
log_warn()  { log "WARN" "$*"; }
log_error() { log "ERROR" "$*"; }

die() {
  log_error "$*"
  exit 1
}

cleanup() {
  local status=$?
  # Add resource cleanup here if needed.
  return "${status}"
}
trap cleanup EXIT

while getopts ":hvn" opt; do
  case "${opt}" in
    h) usage; exit 0 ;;
    v) DEBUG=1 ;;
    n) DRY_RUN=1 ;;
    :) die "Option -${OPTARG} requires a value." ;;
    \?) die "Unknown option: -${OPTARG}" ;;
    *) die "Unhandled option parser state: ${opt}" ;;
  esac
done
shift $((OPTIND - 1))

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

input=$1

main() {
  log_debug "Input: ${input}"

  if [[ ! -e "${input}" ]]; then
    die "Input does not exist: ${input}"
  fi

  if [[ "${DRY_RUN}" == "1" ]]; then
    log_info "Dry run: would process ${input}"
    return 0
  fi

  log_info "Processing ${input}"
  # Implement core logic here.
}

main "$@"
