# Agent Skills

[Agent Skills](https://agentskills.io/home) are folders of instructions, scripts, and resources - typically encoding procedural knowledge - that agents can discover and use to do things more accurately and efficiently.

- `skill.md` is the keystone describing what the skill does, when to use it, and then the procedural knowledge required to complete the task.
- The skill directory may contain other documents, scripts, or resources necessary to enact the instructions as directed by the `skill.md`.
- Skills with python scripts use `uv` to manage their dependencies; you must have `uv` installed.

## Installation

Claude Code, OpenAI Codex, and GitHub Copilot (among others) can all use skills, but they look for skills in different locations.
This instruction assumes installation is intended for a central installation location (e.g., `$HOME/.config/skills`, or wherever you clone this repo) for "globally available" skills; repo-specific skills should be installed in the repo (typically `<repo_path>/{.claude,.codex,.copilot}/skills`).

Symlink skills into the Agent's expected locations:

| Assistant      | Location            |
| -------------- | ------------------- |
| Claude Code    | `~/.claude/skills`  |
| GitHub Copilot | `~/.copilot/skills` |
| OpenAI Codex   | `~/.codex/skills`   |

```sh
for dir in "${PWD}/skills/"*/; do
  name="$(basename "$dir")"
  for target in ~/.claude/skills ~/.copilot/skills ~/.codex/skills; do
    mkdir -p "$target"
    ln -sfn "$dir" "$target/$name"
  done
done
```

## Further reading

- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Skills in OpenAI Codex](https://blog.fsck.com/2025/12/19/codex-skills/)
- [Equipping agents for the real world with Agent Skills \\ Anthropic | Claude](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
- [A complete guide to building skills for Claude | Claude](https://claude.com/blog/complete-guide-to-building-skills-for-claude)
