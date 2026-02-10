# Quoting and Expansion

## Defaults

- Prefer `${VAR}` over `$VAR` in script logic for readability and boundary safety.
- Quote parameter expansions unless you intentionally want splitting/globbing.
- Quote command substitutions: `"$(cmd)"`.
- Prefer `"$@"` over `$*` for forwarding args.

## Why This Matters

- POSIX shell rules treat many characters as special unless quoted.
- In Bash, unquoted expansions can trigger word splitting and filename expansion.
- In Bash `[[ ... ]]`, words do not undergo word splitting or filename expansion.

## Safe Patterns

```bash
name="${1:-}"
printf '%s\n' "${name}"

mapfile -t lines < <(some_command)   # Bash-specific
for item in "${lines[@]}"; do
  printf '%s\n' "${item}"
done
```

## Arrays and Quoting (Bash)

- Use arrays for argument lists: `args=(--flag "${value}" -- "${path}")`.
- Expand arrays as `"${args[@]}"` to preserve element boundaries.
- Avoid `"${args[*]}"` unless a single joined string is intentionally required.

## Intentional Unquoted Cases

Use unquoted expansion only when behavior is explicitly desired and documented:

- Arithmetic contexts: `(( count += step ))`
- Brace/parameter defaults inside assignment where safe.
- Pattern/regex positions in `[[ ... ]]` where quoting would change semantics.

## Common Mistakes

- `for x in $(cmd)` for arbitrary text input.
- Unquoted RHS in `cp "$src" $dst`.
- Assuming braces (`${VAR}`) are equivalent to quoting (they are not).

## Related ShellCheck Codes

- SC2086, SC2046, SC2048, SC2068, SC2206, SC2207, SC2295

## Sources

- [GNU Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html) (quoting, parameter expansion, word splitting)
- [POSIX Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html) (quoting and expansion rules)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html) (quoting conventions)
