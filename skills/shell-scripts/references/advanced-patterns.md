# Advanced Patterns

## Robust Script Lifecycle

Use a cleanup trap and deterministic exit paths.

```bash
tmp_dir=""
cleanup() {
  local status=$?
  if [[ -n "${tmp_dir}" && -d "${tmp_dir}" ]]; then
    rm -rf -- "${tmp_dir}"
  fi
  return "${status}"
}
trap cleanup EXIT
```

## Safe Temporary Resources

```bash
tmp_dir="$(mktemp -d)"
readonly tmp_dir
```

Avoid fixed `/tmp` names.

## Argument Parsing (`getopts`)

Use `getopts` for short flags and explicit usage output.
See `assets/getopts-template.sh`.

## Read Loops Without Mangling

```bash
while IFS= read -r line; do
  printf '%s\n' "${line}"
done < "${input_file}"
```

## Retry with Backoff

```bash
retry() {
  local attempts=$1
  shift
  local i=1
  local delay=1

  while (( i <= attempts )); do
    if "$@"; then
      return 0
    fi
    (( i == attempts )) && return 1
    sleep "${delay}"
    (( delay *= 2, i += 1 ))
  done
}
```

## Arrays for Safe Command Construction (Bash)

```bash
cmd=(rsync -a --delete "${src}/" "${dst}/")
"${cmd[@]}"
```

Use this instead of building one string and evaluating it.

## Cross-OS External Tool Strategy

- Prefer POSIX options for `sed`, `grep`, `awk`, `find`.
- Probe command availability with `command -v`.
- For GNU-specific behavior on macOS, use `g*` variants (`gsed`, `gdate`) if they exist.
- If GNU behavior is required and those commands are missing, suggest installing GNU tools (for example `gnu-sed` and `coreutils`) before proceeding.
- See `references/command-resolution-and-os-portability.md`.

## Agent-Consumed Scripts

When a script's primary consumer is an agent rather than a human:

- Write machine-readable output (JSON, paths, `key=value`) to stdout only; send all diagnostics, progress, and warnings to stderr (`>&2`).
- Exit 0 only on success; return non-zero on any known error.
  Never `exit 0` after printing an error.
- Avoid ANSI color in stdout — agents parse it, they do not render it.
- On invalid input against a fixed set, emit the valid set so the agent self-corrects: `printf 'error: must be one of: a b c (got: %s)\n' "${val}" >&2`.
- Guard destructive operations behind an explicit non-default flag (`--force`, `--delete`); do not make the destructive path the default, since agents retry without human review.

## Avoid Common Footguns

- Do not parse `ls` output.
- Avoid `for x in $(cmd)` for arbitrary text.
- Avoid `eval` unless input is strictly controlled.
- Avoid relying on `set -e` behavior in complex conditionals without tests.

## Sources

- [GNU Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html) (`set -e`, `pipefail`, `inherit_errexit`)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html) (arrays, loops, arithmetic, quoting)
