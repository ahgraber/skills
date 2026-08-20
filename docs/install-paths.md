# Installing skills, and where they land

There are two ways to get these skills into an agent: copy the files into a directory the agent reads, or serve them over MCP.
This page covers both, and documents which directories each agent reads — which turns out to be the more useful fact, because several agents share one.

## Copying with the CLI

The [skills.sh](https://skills.sh) CLI copies skill files into the directory your agent reads:

```bash
# One skill, for the current user, into Claude Code's directory
npx skills add ahgraber/skills --skill commit-message -g

# Several skills, into several agents at once
npx skills add ahgraber/skills --skill code-review --skill simplify -a claude-code -a codex -g

# Into the current project instead of your user directory
npx skills add ahgraber/skills --skill sdd
```

Symlinked references inside this repository are resolved during the copy, so each installed skill is self-contained.
Refresh installed skills with `npx skills update`.

See the [README](../README.md#installation) for the full flag list.

## Where skills land

Most agents read more than one directory, and several honor the vendor-neutral `.agents/skills` convention.

| Agent             | User directories                                                    | Project directories                                                 |
| ----------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------- |
| Claude Code       | `~/.claude/skills`                                                  | `.claude/skills`, including nested ones below the working directory |
| Codex             | `~/.agents/skills`, `/etc/codex/skills`                             | `.agents/skills`, and the repository root's `.agents/skills`        |
| VS Code / Copilot | `~/.copilot/skills`, `~/.claude/skills`, `~/.agents/skills`         | `.github/skills`, `.claude/skills`, `.agents/skills`                |
| OpenCode          | `~/.config/opencode/skills`, `~/.claude/skills`, `~/.agents/skills` | `.opencode/skills`, `.claude/skills`, `.agents/skills`              |
| Pi                | `~/.pi/agent/skills`, `~/.agents/skills`                            | `.pi/skills`, `.agents/skills`                                      |

Two consequences worth acting on.

**`~/.agents/skills` reaches four of these agents at once.**
Codex, VS Code, OpenCode, and Pi all read it.
Installing there once, rather than into each vendor's directory separately, keeps a single copy for all four.

**Claude Code is the exception.**
It reads only `~/.claude/skills` and `.claude/skills`, so it needs its own copy — or a symlink from `~/.claude/skills` to the same content.

OpenCode and Pi also accept explicit directory lists in their configuration, so you can point them at an existing collection instead of copying.
Pi's own documentation demonstrates pointing it at `~/.claude/skills`.

## Serving over MCP

If your agent supports MCP but has no concept of skills, or you would rather not maintain copies at all, the bundled `skills-mcp` server exposes skills as MCP resources from wherever they already live.
It scans the known vendor directories, collapses duplicates that reach the same content by symlink or identical bytes, and serves one copy of each.

See [serving-skills-via-mcp.md](serving-skills-via-mcp.md) for setup, and [`skills-mcp/src/skills_mcp/discovery.py`](../skills-mcp/src/skills_mcp/discovery.py) for the directories it searches, which include several beyond the table above.

## Choosing between copying and serving

Copy when you want a small number of skills in one or two agents, or when you want to read and edit the installed files.
Copies are ordinary files; nothing hides them from you.

Serve when you run several agents, or when you edit skills and want every agent to see the change without a re-copy.
One source of truth, no per-vendor duplication.

The two are not exclusive.
Copying into `~/.agents/skills` and serving the same directory over MCP is a reasonable arrangement.

## Names and precedence

An installed skill keeps its own name, so `code-review` becomes `/code-review`.

In Claude Code, that name can displace a built-in skill.
A skill in `~/.claude/skills` takes precedence over Claude Code's built-in skill of the same name, and a personal skill takes precedence over a project one.
So installing `code-review` here means `/code-review` runs this repository's version rather than the built-in.
That is usually the intent, but it is worth knowing it happens.

To keep a skill installed without letting it announce itself to the model, Claude Code's `skillOverrides` setting can mark one `name-only`, so it stays invocable but stops consuming description budget, or `off` entirely.
That matters more than it sounds: Claude Code loads every skill's name and description into context under a character budget, and when that budget overflows it drops descriptions starting with the skills you invoke least.
An unused skill is not free — it can crowd out the description of one you rely on.

Install what you will use.
