# harness

Work across agent harnesses: drive an agent in another harness over tmux, and author or tune skills.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `agent-bridge`: Use when an agent in one harness must create, observe, or steer one or more agents in another harness through a tmux session the user can watch.
- `optimize-skills`: Use when creating or refining SKILL.md-based skills, or diagnosing weak triggering (under/over-triggering, vague descriptions, bloated context, or missing workflow guidance).

## Install

Skills in this plugin call on the skills in `core`.
Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install harness@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add harness@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install harness@ahgraber-skills
```

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
