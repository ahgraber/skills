# Using Skills with Claude Code on the Web

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
