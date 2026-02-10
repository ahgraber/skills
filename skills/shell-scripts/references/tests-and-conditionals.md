# Tests and Conditionals

## Quick Rule

- Bash-first: prefer `[[ ... ]]`.
- POSIX strict: use `[ ... ]`.

## `[[ ... ]]` (Bash)

- No word splitting or filename expansion inside the test expression.
- Supports `=~` regex matching and pattern matching for `==`/`!=`.
- Better default for Bash scripts to reduce quoting hazards.

```bash
if [[ -n "${path}" && "${path}" == *.sh ]]; then
  :
fi
```

## `[ ... ]` (POSIX)

- Portable across POSIX shells.
- Requires stricter quoting discipline.
- Avoid non-portable operators in POSIX mode.

```sh
if [ -n "${path}" ] && [ "${path##*.}" = "sh" ]; then
  :
fi
```

## Numeric Comparisons

- Prefer arithmetic contexts in Bash: `(( value > 3 ))`.
- For POSIX shells use `-gt`, `-eq`, etc. inside `[ ... ]`.

## Prefer `case` for Pattern Routing

Use `case` instead of long `if` chains for glob-like dispatch.

```bash
case "${mode}" in
  lint) run_lint ;;
  test) run_test ;;
  *) printf 'Unknown mode: %s\n' "${mode}" >&2; exit 2 ;;
esac
```

## Related ShellCheck Codes

- SC2071, SC2074, SC2075, SC2081, SC2107, SC2108, SC2166, SC2292, SC3010

## Sources

- [GNU Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html) (`[[ ... ]]` semantics)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html#test----and---) (`[ ]` vs `[[ ]]` guidance)
- [POSIX Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html) (reserved words and test portability)
