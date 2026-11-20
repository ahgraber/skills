# Compatibility Matrix

Use this file first.
Pick one target before coding.

## Target Modes

| Target mode         | Shebang                                                          | Allowed features                                                         | Recommended tests                         |
| ------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------ | ----------------------------------------- |
| POSIX strict        | `#!/bin/sh`                                                      | POSIX shell only (`[ ]`, `case`, `$(...)`)                               | `sh -n`, `shellcheck -s sh`               |
| Bash-first          | `#!/usr/bin/env bash` (or `#!/bin/bash` if repo policy requires) | Bash features (`[[ ]]`, arrays, `(( ))`, `mapfile`, `shopt`)             | `bash -n`, `shellcheck -s bash`           |
| Bash + zsh-friendly | `#!/usr/bin/env bash`                                            | Prefer POSIX/Bash-overlap; avoid Bash-only edge features unless required | `bash -n`, `zsh -n`, `shellcheck -s bash` |

## Shebang Policy

- Shebang interpreter paths should be absolute.
  ShellCheck SC2239 documents this.
- Use `#!/usr/bin/env bash` when Bash path may vary by environment.
- Use `#!/bin/bash` only when platform policy guarantees Bash there.
- Use `#!/bin/sh` only when you intentionally commit to POSIX syntax.

## POSIX vs Bash Decision Rule

Choose POSIX strict when:

- The script must run under unknown `/bin/sh` implementations.
- Deployment environments include BusyBox/dash/alpine images.
- You do not need arrays, `[[ ]]`, process substitution, or Bash-only options.

Choose Bash-first when:

- The project controls runtime and can guarantee Bash.
- You need Bash arrays, `[[ ... =~ ... ]]`, `mapfile`, `coproc`, or `shopt`.
- Readability improves with Bash constructs and the portability tradeoff is acceptable.

## zsh Compatibility Rule

- zsh docs state compatibility emulation is best effort and not guaranteed complete POSIX emulation.
- If a Bash script must also be zsh-friendly, avoid features with divergent behavior and validate with `zsh -n`.
- Prefer conservative patterns: explicit quoting, simple arrays, `case` for pattern dispatch, and minimal shell-option dependence.

## `[` vs `[[` Rule

- In Bash-first mode, prefer `[[ ... ]]` for most conditionals.
- In POSIX strict mode, use `[ ... ]`.
- If code must run in both Bash and strict POSIX `sh`, use `[ ... ]` and avoid `[[ ... ]]`.

## Command Resolution Rule

- Assume command shadowing is possible in developer environments.
- For critical commands, check with `command -v` and inspect with `type -a` when behavior looks wrong.
- Prefer reproducible command invocation patterns documented in `references/command-resolution-and-os-portability.md`.

## Sources

- [POSIX Shell Command Language](https://pubs.opengroup.org/onlinepubs/9799919799/utilities/V3_chap02.html)
- [GNU Bash Reference Manual](https://www.gnu.org/software/bash/manual/bash.html)
- [zsh Invocation Compatibility](https://zsh.sourceforge.io/Doc/Release/Invocation.html#Compatibility)
- [ShellCheck SC2239](https://www.shellcheck.net/wiki/SC2239)
