#!/usr/bin/env bash
# getopts Template (Bash)

verbose=0
dry_run=0

usage() {
  cat <<USAGE
Usage: $0 [-v] [-n] [-h] <input>
  -v  verbose logging
  -n  dry run
  -h  help
USAGE
}

while getopts ":vnh" opt; do
  case "${opt}" in
    v) verbose=1 ;;
    n) dry_run=1 ;;
    h) usage; exit 0 ;;
    :) printf 'Missing value for -%s\n' "${OPTARG}" >&2; usage; exit 2 ;;
    \?) printf 'Invalid option: -%s\n' "${OPTARG}" >&2; usage; exit 2 ;;
    *) printf 'Unhandled option parser state: %s\n' "${opt}" >&2; usage; exit 2 ;;
  esac
done
shift $((OPTIND - 1))

if [[ $# -lt 1 ]]; then
  usage
  exit 2
fi

input=$1
