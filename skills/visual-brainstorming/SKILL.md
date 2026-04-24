---
name: visual-brainstorming
description: |-
  Browser-based visual companion for brainstorming sessions — showing mockups, wireframes, diagrams, and side-by-side comparisons. Use when a brainstorming question is inherently visual: layout choices, UI mockups, architecture diagrams, design comparisons. Not for: text-based questions, conceptual A/B choices, requirements scope, or tradeoff lists (those stay in terminal). Requires user consent before starting a session.
---

# Visual Brainstorming Companion

A browser-based tool for showing mockups, diagrams, and visual options during brainstorming.
This is a tool — not a mode.
Invoking this skill means the browser is available for questions that benefit from visual treatment; it does NOT mean every question goes through the browser.

## Offering the Companion

When you anticipate that upcoming questions will involve visual content (mockups, layouts, diagrams), offer the companion once for user consent:

> "Some of what we're working on might be easier to explain if I can show it to you in a web browser. I can put together mockups, diagrams, comparisons, and other visuals as we go. This feature is still new and can be token-intensive. Want to try it? (Requires opening a local URL)"

**This offer MUST be its own message.**
Do not combine it with clarifying questions, context summaries, or any other content.
Wait for the user's response before continuing.
If they decline, proceed with text-only brainstorming.

## When to Use the Browser vs Terminal

Decide per-question, not per-session.
The test: **would the user understand this better by seeing it than reading it?**

**Use the browser** when the content itself is visual:

- UI mockups — wireframes, layouts, navigation structures, component designs
- Architecture diagrams — system components, data flow, relationship maps
- Side-by-side visual comparisons — two layouts, two color schemes, two design directions
- Design polish — questions about look and feel, spacing, visual hierarchy
- Spatial relationships — state machines, flowcharts, entity relationships rendered as diagrams

**Use the terminal** when the content is text or tabular:

- Requirements and scope questions — "what does X mean?", "which features are in scope?"
- Conceptual A/B/C choices — picking between approaches described in words
- Tradeoff lists — pros/cons, comparison tables
- Technical decisions — API design, data modeling, architectural approach selection
- Clarifying questions — anything where the answer is words, not a visual preference

A question _about_ a UI topic is not automatically a visual question.
"What kind of wizard do you want?"
is conceptual — use the terminal.
"Which of these wizard layouts feels right?"
is visual — use the browser.

## Starting a Session

After the user consents to the visual companion, ask one question before starting the server:

> "Do you want to save the wireframes from this session? If yes, where should I save them? (Otherwise they'll be cleaned up automatically when we're done.)"

If they want to save: pass `--project-dir <path>` to `start-server.sh`.
If not: start without `--project-dir` and the session cleans up on stop.

## Detailed Guide

Once the user consents, read the detailed guide before proceeding: `skills/visual-brainstorming/visual-companion.md`
