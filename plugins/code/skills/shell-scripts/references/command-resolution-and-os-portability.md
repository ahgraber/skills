# Command Resolution and OS Portability

## 1. Arrays Policy

Use arrays when target is Bash.

- Good for argument vectors and file lists.
- Prevents whitespace/globbing bugs from string concatenation.
- Invoke commands with `"${cmd[@]}"`, not `eval`.

```bash
cmd=(grep -E -- "${pattern}" "${file}")
"${cmd[@]}"
```

If target is POSIX `sh`:

- Do not use arrays.
- Use positional parameters (`set --`) or newline-delimited processing with `while IFS= read -r`.

## 2. Builtins and External Commands

Prefer shell builtins when they are sufficient (`printf`, `read`, `test`/`[`, `case`, arithmetic).

For external commands:

- Resolve command explicitly with `command -v <name>`.
- Inspect full resolution order with `type -a <name>` when shadowing is suspected.
- Use `command <name> ...` to skip shell function lookup when needed.

This helps catch local overrides such as aliases/functions or PATH-precedence replacements.

## 3. Shadowing / Override Checks

When reproducibility matters, verify critical tools before use:

```bash
require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    printf 'Missing required command: %s\n' "$1" >&2
    exit 127
  }
}

require_cmd sed
require_cmd awk
require_cmd grep
```

For debugging odd behavior:

```bash
type -a cat
```

## 4. GNU vs BSD/macOS Differences

Use portable options by default.
Common divergences:

- `sed -i`: GNU allows `-i` without backup suffix; BSD/macOS requires a suffix argument (possibly empty: `-i ''`).
- `date`: GNU supports `-d`; BSD/macOS commonly use `-v` patterns instead.
- `readlink -f`: not portable to macOS default `readlink`.
- `grep -P`: often unavailable in BSD/macOS `grep`.

Practical rule:

- Avoid GNU-only flags unless target environment is pinned.
- If GNU behavior is required on macOS, use `gsed`/`gdate` when available.
- If GNU behavior is required and `gsed`/`gdate` are not available, suggest installing GNU tools (for example `gnu-sed` and `coreutils`) and fail with a clear message.

## 5. Minimal Tool Probing Pattern

```bash
pick_sed() {
  if command -v gsed >/dev/null 2>&1; then
    printf '%s\n' "gsed"
  else
    printf '%s\n' "sed"
  fi
}

SED_BIN="$(pick_sed)"
```

## Sources

- [GNU Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html)
- [POSIX Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)
- [zsh Invocation Compatibility](https://zsh.sourceforge.io/Doc/Release/Invocation.html#Compatibility)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [ShellCheck Wiki](https://www.shellcheck.net/wiki/)
