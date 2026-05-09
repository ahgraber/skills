# Serving Skills via MCP

If your agent supports MCP but does not have native support for skills, you can expose this repo's skills (or any installed skills under `~/.claude/skills`, `~/.agents/skills`, etc.) directly as MCP resources/tools instead of, or in addition to, copying them into vendor directories with `npx skills add`.

The bundled [`skills-mcp/`](../skills-mcp/) is a stdio MCP server that auto-discovers known skill locations, deduplicates by symlink/inode and content hash, and exposes each skill at `skill://{name}/SKILL.md` (plus a synthetic `_manifest` and lazy supporting files).
It also provides generic `list_resources` / `read_resource` tools for clients that don't speak the MCP resources protocol — see its [README](../skills-mcp/README.md) for the full surface.

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
