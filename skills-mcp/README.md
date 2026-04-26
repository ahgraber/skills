# skills-mcp

A stdio MCP server that aggregates [agent skills](https://agentskills.io/home)
from well-known vendor locations (`~/.claude/skills`, `~/.agents/skills`,
`~/.cursor/skills`, etc.) and exposes each as MCP resources via FastMCP's
`SkillsDirectoryProvider`.

Adds a small dedup pipeline on top of FastMCP's built-in scanning:

1. **Symlink/inode collapse** — same skill reachable through multiple roots
   (e.g. `~/.agents/skills/foo` symlinked into `~/.claude/skills/foo`)
   resolves to one resource.
2. **Content-hash collapse** — distinct paths with byte-identical `SKILL.md`
   resolve to one resource.
3. **Namespaced collisions** — when the same skill name has differing content across roots, the first-precedence one keeps the bare name and others are exposed under `skill://{root_label}--{name}/SKILL.md`.
   A warning is logged.

## Install

```bash
uv sync
```

## Run

```bash
# Auto-discover all known vendor roots that exist
uv run skills-mcp

# Add ad-hoc roots (label derived from path tail)
uv run skills-mcp --root ~/work/skills

# Explicit label
uv run skills-mcp --root team=/srv/shared/skills

# Restrict / exclude vendor roots
uv run skills-mcp --include claude --include agents
uv run skills-mcp --exclude opencode --exclude goose

# Skip vendor auto-discovery entirely (only --root entries)
uv run skills-mcp --no-vendor --root ~/my-skills
```

The `SKILLS_MCP_ROOTS` env var accepts a `os.pathsep`-separated list of `PATH` or `LABEL=PATH` entries.

## MCP client config

MCP clients typically launch the server with a stripped `PATH`, so a bare `"command": "uv"` often fails with `No such file or directory: 'uv'`.
Use one of the following — pick whichever matches how you manage tools.

### Option 1 — absolute `uv`, ephemeral env

Resolves dependencies on each launch.
Adjust the path to match `which uv`.

```json
{
  "mcpServers": {
    "skills": {
      "command": "/Users/you/.local/bin/uv",
      "args": [
        "run",
        "--directory",
        "/path/to/skills-mcp",
        "skills-mcp"
      ]
    }
  }
}
```

### Option 2 — `uv tool install` shim

Install once as a user-level tool, then reference the shim.

```bash
uv tool install --editable /path/to/skills-mcp
ls ~/.local/bin/skills-mcp   # confirm
```

The shim is the `skills-mcp` entry point declared in `pyproject.toml`, so `args` accepts any flag from `skills-mcp --help` (`--root`, `--include`, `--exclude`, `--no-vendor`, `--reload`, `--log-level`, …).
None are required — the bare command auto-discovers known vendor roots.

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

With explicit flags, e.g. restricting to your two main roots and adding an extra:

```json
{
  "mcpServers": {
    "skills": {
      "command": "/Users/you/.local/bin/skills-mcp",
      "args": [
        "--include",
        "claude",
        "--include",
        "agents",
        "--root",
        "team=/srv/shared/skills"
      ]
    }
  }
}
```

## Discovery precedence

CLI `--root` entries → `SKILLS_MCP_ROOTS` env → known vendor roots in this order: `project` (`$CWD/.claude/skills`), `claude`, `agents`, `cursor`, `codex`, `gemini`, `copilot`, `opencode`, `goose`.
Earlier entries win name collisions.

## URIs

- `skill://{name}/SKILL.md` — the skill's main instruction file.
- `skill://{name}/_manifest` — synthetic JSON listing of all files in the skill.
- `skill://{name}/{path}` — supporting files (lazy template by default).

## Tools-only clients (`--expose`)

Some MCP clients don't implement the resources protocol.
By default (`--expose both`) the server also surfaces the same skills via FastMCP's `ResourcesAsTools` transform, which adds two generic tools:

- `list_resources()` — returns metadata for every skill resource and template.
- `read_resource(uri)` — reads a `skill://...` URI; routes through the same provider stack as native resource reads.

```bash
uv run skills-mcp                      # both surfaces (default)
uv run skills-mcp --expose tools       # only the resource-proxy tools
uv run skills-mcp --expose resources   # only native MCP resources
```

Progressive disclosure is preserved without bloating the tool list:

- **Tier 1** — the MCP `instructions` field is populated with a compact index of every available skill (name + frontmatter description) plus the URI scheme cheat-sheet, so the agent sees what's available ambiently in the system prompt.
- **Tier 2** — `read_resource("skill://name/SKILL.md")` loads the full instruction body on demand.
- **Tier 3** — `read_resource("skill://name/_manifest")` enumerates supporting files; `read_resource("skill://name/path/to/file")` fetches them.

## Dev / debug

[`@modelcontextprotocol/inspector`](https://github.com/modelcontextprotocol/inspector) is the easiest way to poke at the server without wiring it into a real client.
It spawns the server, attaches via stdio, and opens a browser UI at `http://localhost:6274` where you can list/call tools, browse resources, and read individual resource bodies.

```bash
# Run against the local checkout (auto-discovers vendor roots)
npx @modelcontextprotocol/inspector uv run --directory /path/to/skills-mcp skills-mcp

# Or run against the installed shim (after `uv tool install --editable .`)
npx @modelcontextprotocol/inspector skills-mcp --include claude --include agents

# Pin to an isolated set of skills for repeatable debugging
npx @modelcontextprotocol/inspector skills-mcp --no-vendor --no-env --root /tmp/sample-skills
```

Useful checks when iterating:

- **Tier-1 disclosure** — open the server card; the `instructions` panel should show the skill index.
- **Dedup result** — `list_resources` should show one entry per resolved skill; namespaced collisions appear as `skill://{label}--{name}/SKILL.md`.
- **Tools-only path** — under `tools/list` you should see `list_resources` and `read_resource`; calling `read_resource` with a `skill://...` URI must return the same bytes as a native resource read.
- **Reload** — start with `--reload`, edit a `SKILL.md`, then refetch the resource to confirm the change is picked up without restarting.

Bump `--log-level DEBUG` if you want to see per-skill load and dedup decisions in the server's stderr.

## Testing

```bash
uv run pytest
```
