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

## Serving via MCP

If your agent supports MCP but does not have native support for skills, you can expose this repo's skills (or any installed skills under `~/.claude/skills`, `~/.agents/skills`, etc.) directly as MCP resources/tools instead of, or in addition to, copying them into vendor directories with `npx skills add`.

The bundled [`skills-mcp/`](./skills-mcp/) is a stdio MCP server that auto-discovers known skill locations, deduplicates by symlink/inode and content hash, and exposes each skill at `skill://{name}/SKILL.md` (plus a synthetic `_manifest` and lazy supporting files).
It also provides generic `list_resources` / `read_resource` tools for clients that don't speak the MCP resources protocol — see its [README](./skills-mcp/README.md) for the full surface.

Quick install + wire-up:

```bash
# One-time install as a user-level tool
cd skills-mcp
uv tool install --editable .

# Then in your MCP client config (e.g. ~/.claude/settings.json), absolute path
# to the shim avoids PATH issues when the client launches subprocesses:
```

```json
{
  "mcpServers": {
    "skills": {
      "command": "/Users/you/.local/bin/skills-mcp",
      "args": []
    }
  }
}
```

Why use the MCP server instead of (or alongside) `npx skills add`?

- One source of truth — edit a skill once in its source location; every connected agent sees the change immediately, no per-vendor copy/sync.
- Fewer files on disk — no duplicate skill trees per agent vendor.
- Survives multi-vendor setups — symlinking `~/.claude/skills` ↔ `~/.agents/skills` is fine; the server collapses identical content.

## Repository Notes

Some skill families leverage symlinks to reduce drift in replicated components.
Contributors should enable symlink checkout in this repo after cloning: `git config core.symlinks true`.
Symlinks + git work best on macOS/Linux; symlink behavior on Windows can break depending on `core.symlinks` and user permissions.

**Note on optimize-skills**: This skill requires [`graphviz`](https://www.graphviz.org/download/) available on the system.

**Note on mcp-research**: This skill assumes context7, exa, and/or jina mcp servers are available.

**Note on sdd skills**: `skills/sdd/references`is the source of truth for shared SDD files.
Replicated copies in `skills/sdd-*` are implemented as symlinks to reduce drift.

**Note on spec-kit skills**: `skills/spec-kit/scripts` and `skills/spec-kit/references` are the source of truth for shared Spec Kit files.
Replicated copies in `skills/spec-kit-*` are implemented as symlinks to reduce drift.

## Using Skills with Claude Code on the Web

1. Configure the Claude Code startup script.

```sh
#!/bin/bash
set -euo pipefail

# Ensure uv is available
if ! command -v uv &>/dev/null; then
  curl -LsSf https://astral.sh/uv/install.sh | sh
fi
export PATH="$HOME/.local/bin/uv/tools/bin:$PATH"
export PATH="$HOME/.local/share/uv/tools/bin:$PATH"
export PATH="$(uv tool bin):$PATH"

# Sync venv if a pyproject.toml exists
if [ -f "pyproject.toml" ]; then
  uv sync
fi

# Ensure prek is installed as a uv tool
if ! command -v prek &>/dev/null; then
  uv tool install prek
fi

# Install git hooks if a pre-commit config exists
if [ -f ".pre-commit-config.yaml" ]; then
  prek install
fi


# Ensure code-review-graph is installed as a uv tool
if ! command -v code-review-graph &>/dev/null; then
  uv tool install code-review-graph
fi
if command -v code-review-graph &>/dev/null; then
  code-review-graph install --platform claude-code
fi

npx --yes skills \
  add ahgraber/skills \
  --yes \
  --agent claude-code \
  --skill pr-review commit \
    api-design \
    code-review \
    commit-message \
    handoff \
    mcp-research \
    python \
    python-concurrency-performance \
    python-data-state \
    python-design-modularity \
    python-errors-reliability \
    python-integrations-resilience \
    python-notebooks-async \
    python-runtime-operations \
    python-testing \
    python-types-contracts \
    python-workflow-delivery \
    sdd \
    sdd-apply \
    sdd-archive \
    sdd-derive \
    sdd-explore \
    sdd-propose \
    sdd-sync \
    sdd-translate \
    sdd-verify \
    shell-scripts
```

2. Add a local hook (`./.claude/settings.json`) to inform Claude that these skills are now available (Claude on the web only sees a standard Anthropic-provided set).
   This file must be committed to the repo so it is pulled into the Claude Code on the web environment.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "echo 'Installed skills:'; ls ~/.claude/skills/ 2>/dev/null; ls .claude/skills/ 2>/dev/null"
          }
        ]
      }
    ]
  }
}
```

## Further reading

- [Claude Agent Skills: A First Principles Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)
- [Skills in OpenAI Codex](https://blog.fsck.com/2025/12/19/codex-skills/)
- [Equipping agents for the real world with Agent Skills \\ Anthropic | Claude](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
- [A complete guide to building skills for Claude | Claude](https://claude.com/blog/complete-guide-to-building-skills-for-claude)
