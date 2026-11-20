# Installing the skills as plugins

The skills are published as plugins for Claude Code, Codex, and GitHub Copilot (CLI and VS Code), from one marketplace in this repository.
A plugin installs a group of skills at once, and the agent's plugin manager updates it.

## Plugins

| Plugin     | Skills                                                                                                                      |
| ---------- | --------------------------------------------------------------------------------------------------------------------------- |
| `core`     | commit-message, receiving-feedback, subagent-patterns                                                                       |
| `sdd`      | sdd, sdd-apply, sdd-archive, sdd-derive, sdd-explore, sdd-propose, sdd-sync, sdd-translate, sdd-verify, formal-verification |
| `code`     | api-design, changelog, code-review, debugging, jj, refactor, securing-code, shell-scripts, simplify, writing-tests          |
| `python`   | python, python-notebooks-async, interactive-notebook-demo, writing-docstrings                                               |
| `security` | security-scan, security-deep-scan, security-triage-finding, security-fix-finding                                            |
| `thinking` | brainstorming, grill-me, handoff, show-me, teach-me                                                                         |
| `writing`  | alt-text, antislop-writing, editorial-review, proof, synthesize                                                             |
| `research` | deep-research, mcp-research, and the [Jina](https://jina.ai) MCP server                                                     |
| `harness`  | agent-bridge, optimize-skills                                                                                               |

`strudel` is not in a plugin; install it with `npx skills`.

## Installing

Skills in every other plugin call on the skills in `core`, so install `core` alongside any plugin you choose.
Claude Code installs it for you as a dependency; Codex and Copilot do not.

```bash
# Claude Code (installs core automatically)
claude plugin marketplace add ahgraber/skills
claude plugin install code@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add code@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install code@ahgraber-skills
```

Use one install method per agent: plugins or `npx skills`, not both.
Claude Code and Codex would list each skill twice, once as `commit-message` and once as `core:commit-message`, and Copilot would silently use the `npx skills` copy.

## Names

Claude Code and Codex prefix a plugin's skills with the plugin name, so `commit-message` from `core` is `/core:commit-message`.
The skills refer to each other by bare name, and Claude Code resolves that name to the prefixed one.

Copilot and VS Code use the bare name and keep only one skill per name.
A skill here can hide, or be hidden by, a same-named skill from another plugin or from your own skill directories.

## Updating

Plugin versions follow the skills collection's release tags.
Claude Code and Codex update an installed plugin only when its version changes, so changes between releases reach plugin users at the next `skills-v` release; `npx skills update` picks them up sooner.

```bash
claude plugin update code@ahgraber-skills
codex plugin marketplace upgrade ahgraber-skills
copilot plugin update code@ahgraber-skills
```

## The Jina MCP server and its API key

The `research` plugin registers the hosted [Jina](https://jina.ai) MCP server for web search and page reads.
`deep-research` and `mcp-research` work with any docs, search, or reader server you have, such as Context7, Exa, or Perplexity; Jina is a default, not a requirement.

Jina works without an API key, at its anonymous rate limits.
In Claude Code, the plugin has an optional `jina_api_key` setting that raises them.
Set it in the `/plugin` menu, at install with `--config jina_api_key=<key>`, or afterwards:

```bash
printf '%s' '{"jina_api_key":"<key>"}' | claude plugin configure research@ahgraber-skills --values-stdin
```

Restart Claude Code to apply it.
In Codex and Copilot, the Jina server runs without a key: Codex drops the plugin's MCP headers, and Copilot sends the unfilled `${user_config.jina_api_key}` text, which Jina ignores.
