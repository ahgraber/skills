# Installing the skills

There are three ways to get these skills into an agent:

- [Copy them with skills.sh](skills-sh.md): `npx skills` copies the skills you pick into a directory the agent reads.
  This is the default, and it works with any agent that reads skill directories.
- [Install them as plugins](plugins.md): Claude Code, Codex, and GitHub Copilot (CLI and VS Code) install groups of skills from this repository's plugin marketplace and update them with their own plugin commands.
  The `research` plugin also registers the Jina MCP server.
- [Serve them over MCP](../serving-skills-via-mcp.md): the bundled `skills-mcp` server exposes skills as MCP resources from wherever they already live, for agents that support MCP but have no concept of skills.

## Choosing a method

Copy when you want a small number of skills in one or two agents, or when you want to read and edit the installed files.
Copies are ordinary files; nothing hides them from you.

Install plugins when you want a whole group of skills in Claude Code, Codex, or Copilot and want updates to arrive through the agent's plugin manager at each release.

Serve when you run several agents, or when you edit skills and want every agent to see the change without a re-copy.
The `skills-mcp` server scans the known vendor directories, collapses duplicates that reach the same content by symlink or identical bytes, and serves one copy of each.
See [`skills-mcp/src/skills_mcp/discovery.py`](../../skills-mcp/src/skills_mcp/discovery.py) for the directories it searches.

Copying and serving are not exclusive.
Copying into `~/.agents/skills` and serving the same directory over MCP is a reasonable arrangement.

Do not combine plugins and `npx skills` in one agent.
Claude Code and Codex list each skill twice, once as `commit-message` and once as `core:commit-message`, and Copilot silently uses the `npx skills` copy.

For a cloud session, see [claude-code-on-web.md](../claude-code-on-web.md).
