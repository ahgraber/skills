# Agent Skills

[Agent Skills](https://agentskills.io/home) are folders of instructions, scripts, and resources - typically encoding procedural knowledge - that agents can discover and use to do things more accurately and efficiently.

- `skill.md` is the keystone describing what the skill does, when to use it, and then the procedural knowledge required to complete the task.
- The skill directory may contain other documents, scripts, or resources necessary to enact the instructions as directed by the `skill.md`.
- Skills with python scripts use `uv` to manage their dependencies; you must have `uv` installed.

## Usage

Skills can be invoked automatically if the underlying agent determines they may be useful (based on the skill's `description`, so tune the description to tune trigger relevance).
Many agents also allow forcibly invoking the skill by invoking as a `/-command`.

## Installation

Install skills using the [skills.sh](https://skills.sh) CLI:

```bash
# List available skills before installing
npx skills add ahgraber/skills --list

# Install all skills interactively (prompts for selection)
npx skills add ahgraber/skills -g

# Install specific skills to user scope (global)
npx skills add ahgraber/skills --skill good-prose --skill mcp-research -g

# Install to specific agents
npx skills add ahgraber/skills --skill good-prose -a claude-code -a codex -g

# Install to current project (instead of global)
npx skills add ahgraber/skills --skill code-review
```

**CLI Options:**

| Flag                      | Purpose                                               |
| ------------------------- | ----------------------------------------------------- |
| `-g, --global`            | Install to user directory (global for all projects)   |
| `-a, --agent <agents...>` | Target specific agents (`claude-code`, `codex`, etc.) |
| `-s, --skill <skills...>` | Install specific skills by name                       |
| `-l, --list`              | List available skills without installing              |
| `-y, --yes`               | Skip confirmation prompts                             |

**Other commands:**

```bash
npx skills list          # Show installed skills
npx skills remove <name> # Uninstall a skill
npx skills update        # Update all installed skills
```

## Repository Notes

Some skill families leverage symlinks to reduce drift in replicated components.
Contributors should enable symlink checkout in this repo after cloning: `git config core.symlinks true`.
Symlinks + git work best on macOS/Linux; symlink behavior on Windows can break depending on `core.symlinks` and user permissions.

**Note on optimize-skills**: This skill requires [`graphviz`](https://www.graphviz.org/download/) available on the system.

**Note on mcp-research**: This skill assumes context7, exa, and/or jina mcp servers are available.

**Note on spec-kit skills**: `skills/spec-kit/scripts` and `skills/spec-kit/references` are the source of truth for shared Spec Kit files.
Replicated copies in `skills/spec-kit-*` are implemented as symlinks to reduce drift.

## Further reading

- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Skills in OpenAI Codex](https://blog.fsck.com/2025/12/19/codex-skills/)
- [Equipping agents for the real world with Agent Skills \\ Anthropic | Claude](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
- [A complete guide to building skills for Claude | Claude](https://claude.com/blog/complete-guide-to-building-skills-for-claude)
