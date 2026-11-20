# writing

Draft and edit prose that reads as a professional wrote it: de-slop, proofread, editorial sparring, synthesis, and alt text.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `alt-text`: Use when the user shares an image, chart, diagram, screenshot, or figure and needs it described — for alt-text, accessibility, documentation, or to understand what it depicts.
- `antislop-writing`: Write, rewrite, or line-edit prose so it reads as a professional wrote it, not a model: clear, specific, register-appropriate, and free of AI writing tells.
- `editorial-review`: Use when the user wants rigorous, non-sycophantic editorial feedback on a draft, essay, blog post, or argument through back-and-forth dialogue — pressure-testing thesis, structure, argument, clarity, tone, and evidence.
- `proof`: Use when the user asks for proofreading or light copy editing while preserving original wording, tone, and order.
- `synthesize`: Use when distilling the through-line gist of one or more sources — the spine, argument, tension, or recurring frame running through a set of documents, notes, research, or transcripts, OR across the ideas within a single rich piece — into a few concise paragraphs.

## Install

Skills in this plugin call on the skills in `core`.
Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install writing@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add writing@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install writing@ahgraber-skills
```

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
