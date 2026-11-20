# security

Scan repositories, pull requests, and supplied findings for vulnerabilities, then triage and fix what proves real.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `security-deep-scan`: Use when the user asks for a deep, exhaustive, multi-pass, or variance-reducing repository-wide or scoped-path security scan.
- `security-fix-finding`: Use when the user explicitly asks to fix and verify a validated or plausible security finding.
- `security-scan`: Use when the user asks for a security scan or review of a repository, a scoped path (package, folder, or submodule), or a Git-backed change set (pull request, commit, branch diff, or working-tree patch).
- `security-triage-finding`: Use when the user supplies existing security findings or vulnerability reports — SARIF results, CVE/GHSA or advisory text, scanner tickets, bug bounty reports, or finding artifacts — and wants static repo-impact triage.

## Install

Skills in this plugin call on the skills in `core`.
Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install security@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add security@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install security@ahgraber-skills
```

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
