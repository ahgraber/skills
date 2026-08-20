# Using Skills with Claude Code on the Web

Cloud sessions (claude.ai/code, `claude --cloud`, routines, Claude Tag) start from a fresh Ubuntu VM with your repository cloned.
They never read `~/.claude/` from your machine, so skills you installed locally are not there.
Three routes get skills into a session; this page covers the setup-script route, which installs this repo's skills on the VM.

| Route                  | How                                                                                 | Notes                                                                                              |
| ---------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Setup script (below)   | Install from this repo onto the VM at environment build time                        | One environment config, works in every repo you open; nothing added to the repo                    |
| Repo `.claude/skills/` | Commit the skill directories to the repository                                      | Per-repo; the skills become part of the clone and of every diff                                    |
| Account skills         | Enable skills for your claude.ai account; cloud sessions load them at session start | Requires uploading each skill to claude.ai; frontmatter is limited to the Agent Skills spec fields |

Plugins declared in a repo's `.claude/settings.json` also install at session start, but this repo does not publish a plugin marketplace manifest.

## 1. Configure the environment's setup script

Add this as the **Setup script** in the cloud environment dialog at [claude.ai/code](https://claude.ai/code) (the cloud icon above the message box).

```sh
#!/bin/bash
# Setup scripts run as root, must exit 0 (a non-zero exit fails session start),
# and should finish within ~5 minutes. The resulting filesystem is snapshotted
# and reused by later sessions, so installs here happen once, not per session.
set -uo pipefail

# uv, ruff, and pytest ship in the image; there is no need to install uv.
# PATH exports here do not reach Claude's shell, so put uv tools somewhere
# already on PATH.
export UV_TOOL_BIN_DIR=/usr/local/bin

# Sync venv if a pyproject.toml exists
if [ -f "pyproject.toml" ]; then
  uv sync || true
fi

# Install git hooks if a pre-commit config exists
uv tool install prek || true
if [ -f ".pre-commit-config.yaml" ]; then
  prek install || true
fi

# Knowledge graph for code review
uv tool install code-review-graph || true
code-review-graph install --platform claude-code || true

npx --yes skills \
  add ahgraber/skills \
  --yes \
  --global \
  --agent claude-code \
  --skill api-design \
    changelog \
    code-review \
    commit-message \
    debugging \
    grill-me \
    handoff \
    mcp-research \
    python \
    python-notebooks-async \
    receiving-feedback \
    refactor \
    sdd \
    sdd-apply \
    sdd-archive \
    sdd-derive \
    sdd-explore \
    sdd-propose \
    sdd-sync \
    sdd-translate \
    sdd-verify \
    securing-code \
    security-scan \
    shell-scripts \
    show-me \
    simplify \
    subagent-patterns \
    teach-me \
    writing-tests || true

exit 0
```

Notes on the environment:

- The default **Trusted** network level reaches npm and PyPI, so `npx` and `uv tool install` work.
  It does not reach `astral.sh`, so installing or self-updating uv needs a **Custom** allowlist that adds that host.
- `--global` installs to the VM's `~/.claude/skills/`, keeping the skills out of the cloned repository and its diffs.
- The setup script re-runs only when you edit it, when you change the allowed domains, or when the snapshot expires (about seven days).
- Use a repo `SessionStart` hook, not the setup script, for project setup that should also run locally.

## 2. Verify the skills are loaded

Add a local hook (`./.claude/settings.json`) that lists the installed skills at session start.
This file must be committed to the repo so it is pulled into the cloud session.

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "if [ \"$CLAUDE_CODE_REMOTE\" = \"true\" ]; then echo 'Installed skills:'; ls ~/.claude/skills/ .claude/skills/ 2>/dev/null; fi; exit 0"
          }
        ]
      }
    ]
  }
}
```

`CLAUDE_CODE_REMOTE` is `true` only in cloud sessions, so the hook stays quiet locally.
If the listing comes back empty, the session runs as a different user than the setup script; drop `--global` so the skills land in the project's `.claude/skills/` instead.
