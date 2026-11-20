# code

Review, reshape, and ship code: review, simplify, refactor, debug, test, API design, shell, secure coding, changelogs, and Jujutsu.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `api-design`: Use when designing, reviewing, or planning REST or GraphQL APIs — endpoint structure, schema design, versioning, error handling, pagination, URI naming, or choosing between REST and GraphQL.
- `changelog`: Use when writing, updating, or generating a CHANGELOG.md — for a new release, an unreleased section update, or drafting from git history or diff.
- `code-review`: Use when reviewing code changes before committing or merging — staged diffs, branch diffs, or PR readiness checks.
- `debugging`: Use when a bug, test failure, build break, regression, flaky test, or unexpected behavior appears — before proposing or attempting fixes.
- `jj`: Use when the repository uses Jujutsu (jj): a `.jj` directory sits at the repo root, `jj root` succeeds, or the user mentions jj, jujutsu, bookmarks, change IDs, or the op log.
- `refactor`: Use when changing the structure of working code without changing its behavior: decomposing an oversized function, extracting or merging a module, collapsing a layer, breaking an import cycle.
- `securing-code`: Use when writing or reviewing code that handles external input, manages access, touches data or crypto, or changes dependencies.
- `shell-scripts`: Use when writing or reviewing Bash scripts and shell snippets, especially for shebang selection, quoting, parameter expansion ("${VAR}" style), test expressions (`[ ]` vs `[[ ]]`), ShellCheck-guided fixes, and portability decisions across POSIX sh, Bash, and zsh compatibility targets.
- `simplify`: Use to cut slop out of working code: duplication, dead code, needless indirection, comment noise, defensive padding.
- `writing-tests`: Use when writing or reviewing tests in any language, or diagnosing a suite that is slow, brittle, or hard to read.

## Install

Skills in this plugin call on the skills in `core`.
Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install code@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add code@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install code@ahgraber-skills
```

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
