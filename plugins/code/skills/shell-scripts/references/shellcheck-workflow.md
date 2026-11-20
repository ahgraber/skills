# ShellCheck Workflow

Use ShellCheck as the default static-analysis gate for shell scripts.

## Command Pattern

```bash
shellcheck -x path/to/script.sh
```

- Use `-s bash` or `-s sh` when the target shell is explicit.
- Use `-x` when scripts source local files.

## Two-Pass Remediation Budget

Apply fixes in at most two passes unless the user explicitly asks for more.

1. Pass 1:

   - Fix correctness and safety issues first.
   - Prioritize quoting, globbing, unsafe deletion, undefined vars, and trap issues.

2. Pass 2:

   - Re-run ShellCheck.
   - Fix remaining practical/high-confidence findings.
   - Stop and report unresolved findings with rationale.

## Prioritization Heuristics

Fix first:

- Safety risks (example: SC2115 unsafe rm patterns)
- Word splitting/globbing hazards (SC2086, SC2046)
- Exit-code/flow hazards (SC2181, SC2015)
- Portability violations against declared target (SC30xx in POSIX mode)

Fix second:

- Readability and minor style recommendations where low risk.

## Suppressions

- Use `# shellcheck disable=SCxxxx` only with a one-line rationale.
- Keep suppressions narrow in scope.
- Do not suppress a warning when a direct code fix is straightforward.

## Shebang and Target Shell Checks

- Ensure shebang matches the declared target.
- If script says `#!/bin/sh`, treat Bash-specific diagnostics as real portability defects.
- If script says Bash, prefer Bash-safe idioms and `[[ ... ]]` where appropriate.

## Reference

- Full code catalog: `references/shellcheck-codes.md`

## Sources

- [ShellCheck Wiki](https://www.shellcheck.net/wiki/) (sitemap and rule pages)
- [ShellCheck SC2239](https://www.shellcheck.net/wiki/SC2239) (shebang path)
