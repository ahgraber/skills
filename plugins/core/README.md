# core

Skills the other plugins call on: subagent dispatch, assessing feedback, and commit messages.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `commit-message`: Use whenever a Conventional Commit message is being drafted — whether the user asks ("write commit message", "draft commit from staged changes", "generate conventional commit", "split this into commits") or you are about to propose one proactively after finishing work (e.g. completing tasks, wrapping up a feature, or summarizing staged changes).
- `receiving-feedback`: You MUST use this when receiving feedback that evaluates a text-based work artifact you produced or are responsible for — code, specs, design docs, PRDs, proposals, plans, or prose — by asserting a defect, questioning a decision, supplying reasoning, or proposing a change for assessment.
- `subagent-patterns`: Use when dispatching development work to one or more subagents and deciding how to shape each dispatch.

## Install

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install core@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
```

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
