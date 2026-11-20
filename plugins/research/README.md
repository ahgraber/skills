# research

Sourced research: multi-source reports and current library, API, and version facts from MCP tools.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `deep-research`: Use when the user wants a deep, multi-source, fact-checked web research report on a topic too broad for a single search.
- `mcp-research`: Use when tasks require current, source-backed technical information from MCP tools.

## Install

Skills in this plugin call on the skills in `core`.
Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install research@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add research@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install research@ahgraber-skills
```

## MCP servers

This plugin registers these MCP servers:

- `jina`: https://mcp.jina.ai/v1

Privacy policy of the server provider: https://jina.ai/legal/#privacy-policy

In Claude Code, set these options in the `/plugin` menu or with `claude plugin configure research@ahgraber-skills`:

- `jina_api_key`: Raises rate limits on the Jina MCP endpoint. Optional; the endpoint also serves unauthenticated requests.

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
