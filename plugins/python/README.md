# python

Python house-style audit, docstrings, notebook event loops, and demo notebooks.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `interactive-notebook-demo`: Use when authoring or reviewing a hands-on demo, tour, or walkthrough notebook (`#%%` percent-format or Jupyter) that demonstrates a feature, library, or API and doubles as semi-interactive documentation.
- `python`: Use when a Python change is about to be called done (before commit or PR) and whenever asked to review, audit, sanity-check, or clean up Python code or judge whether it meets standards.
- `python-notebooks-async`: Use when writing or reviewing asyncio code in Jupyter notebooks or '#%%' cell workflows — structuring event-loop ownership, orchestrating async tasks, or choosing compatibility strategies.
- `writing-docstrings`: Use when writing, rewriting, or auditing Python docstrings that a documentation site is generated from, or when docstrings are long, narrate the code, or leave a reader of the generated reference unable to find their way.

## Install

Skills in this plugin call on the skills in `core`.
Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install python@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add python@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install python@ahgraber-skills
```

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
