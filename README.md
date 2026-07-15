# Agent Skills

[Agent Skills](https://agentskills.io/home) are folders of instructions, scripts, and resources - typically encoding procedural knowledge - that agents can discover and use to do things more accurately and efficiently.

- `skill.md` is the keystone describing what the skill does, when to use it, and then the procedural knowledge required to complete the task.
- The skill directory may contain other documents, scripts, or resources necessary to enact the instructions as directed by the `skill.md`.
- Skills with python scripts use `uv` to manage their dependencies; you must have `uv` installed.

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
npx skills add ahgraber/skills --skill antislop-writing --skill mcp-research -g

# Install to specific agents
npx skills add ahgraber/skills --skill antislop-writing -a claude-code -a codex -g

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

### Serving Skills via MCP

See [docs/serving-skills-via-mcp.md](docs/serving-skills-via-mcp.md) for how to expose this repo's skills as MCP resources/tools using the bundled [`skills-mcp/`](./skills-mcp/) stdio server.

### Using Skills with Claude Code on the Web

See [docs/claude-code-on-web.md](docs/claude-code-on-web.md) for the startup script and `SessionStart` hook needed to surface this repo's skills inside Claude Code on the web.

## Repository Notes

Some skill families leverage symlinks to reduce drift in replicated components.
Contributors should enable symlink checkout in this repo after cloning: `git config core.symlinks true`.
Symlinks + git work best on macOS/Linux; symlink behavior on Windows can break depending on `core.symlinks` and user permissions.

**Note on optimize-skills**: This skill requires [`graphviz`](https://www.graphviz.org/download/) available on the system.

**Note on mcp-research**: This skill assumes [context7](https://context7.com/docs/resources/all-clients), [exa](https://github.com/exa-labs/exa-mcp-server), and/or [jina](https://github.com/jina-ai/MCP) MCP servers are available.

**Note on sdd skills**: `skills/sdd/references`is the source of truth for shared SDD files.
Replicated copies in `skills/sdd-*` are implemented as symlinks to reduce drift.

**Note on spec-kit skills**: `skills/spec-kit/scripts` and `skills/spec-kit/references` are the source of truth for shared Spec Kit files.
Replicated copies in `skills/spec-kit-*` are implemented as symlinks to reduce drift.

**Note on tests**: Tests for skill scripts live at the repo root under `tests/<skill_name>/`, kept out of the skill directories so they are not installed with the skill.
Each test is a `uv` script that declares its own dependencies; run it with `uv run tests/<skill_name>/test_<name>.py`.

## Further Reading

- [Equipping agents for the real world with Agent Skills \\ Anthropic | Claude](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
- [A complete guide to building skills for Claude | Claude](https://claude.com/blog/complete-guide-to-building-skills-for-claude)
- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Skills in OpenAI Codex](https://blog.fsck.com/2025/12/19/codex-skills/)

## Contributing

These skills are developed around my use and workflows.
I'm going to keep iterating and optimizing for me, so suggestions that drift from my workflows may not land.
However, if your use aligns, then I'm happy to co-optimize.

**Skills: Bug reports welcome.**
File an issue with:

- The task you were trying to do.
- The skill(s) involved, from this repo and any others (in case of interaction effects).
- What the agent did that you didn't like, and what you'd have preferred.
- The agent's reply when you ask it "why did you do X?"
  or "why didn't you do Y?"

**MCP servers: Bug reports and PRs welcome.**
Open an issue to discuss first; PRs should include a brief rationale with the change (and tests where applicable).

**Submitting a PR means you've read every line and own your contribution.**
You must specify if and how AI helped draft any part of your contribution (AI support is fine, but must be disclosed).

[stopsloppypasta.ai](https://stopsloppypasta.ai).
