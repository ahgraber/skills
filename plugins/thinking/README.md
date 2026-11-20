# thinking

Think before building: brainstorming, elicitation interviews, visual explanation, lessons, and session handoffs.

A plugin from the `ahgraber-skills` marketplace for Claude Code, Codex, and GitHub Copilot.

## Skills

- `brainstorming`: Use when turning a fuzzy idea into a refined design through dialogue — across software, writing, talks, events, naming, activities, or any creative/design task.
- `grill-me`: Use when the user wants an elicitative interview — reaching alignment on a plan, decision, or idea by drawing out their decisions, unstated opinions, silent assumptions, and thoughts they find hard to put into words, through rounds of pointed questions.
- `handoff`: Use when ongoing work or conversational context must continue in a new conversation, session, or agent with no shared history.
- `show-me`: Use when the user needs to see something to answer the current question — a sketch of logic, runtime flow, UI structure, or file layout; a Mermaid diagram; a chart of the data at hand; a mockup, wireframe, or side-by-side comparison during a design discussion (visual brainstorming).
- `teach-me`: Use when the user wants to be taught a subject, not just answered — "teach me X", "help me learn X", "help me understand X", "help me grok X", "explain how X works", "quiz me on X", "I keep bouncing off X" — where X can be anything: a historical period, a statistical method, music theory, a poem, a legal concept, a cooking technique, a library, a codebase, or a code change.

## Install

Skills in this plugin call on the skills in `core`.
Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.

```bash
# Claude Code
claude plugin marketplace add ahgraber/skills
claude plugin install thinking@ahgraber-skills

# Codex
codex plugin marketplace add ahgraber/skills
codex plugin add core@ahgraber-skills
codex plugin add thinking@ahgraber-skills

# GitHub Copilot CLI; VS Code picks up plugins installed this way
copilot plugin marketplace add ahgraber/skills
copilot plugin install core@ahgraber-skills
copilot plugin install thinking@ahgraber-skills
```

See the [plugin install guide](https://github.com/ahgraber/skills/blob/main/docs/install/plugins.md) for skill names, updates, and API keys.
