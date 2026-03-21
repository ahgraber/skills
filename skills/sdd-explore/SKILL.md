---
name: sdd-explore
description: |-
  Use when the user wants to think through ideas, investigate problems, or clarify requirements before or during any SDD path. A thinking-partner skill — no fixed steps, no mandatory output, no code. Triggers: "explore", "think through", "help me figure out", "what should I build", "I'm not sure where to start", "let's brainstorm", "investigate this", "I want to explore".
---

# SDD Explore

Thinking partner for spec-driven development.
No fixed steps, no mandatory output.
Available before or during any SDD path.

## When to Use

- Before starting any SDD workflow — explore before speccing
- When requirements are unclear and writing a spec would be premature
- During change work when a decision blocks progress
- When you want to investigate the codebase before deciding what to spec

## When Not to Use

- You already know what to build — jump to `sdd-propose` or `sdd-derive`
- You have existing specs to convert — use `sdd-translate`

## Hard Rule: No Code

**Never write or implement code in this skill.**

Reading files and searching the codebase is fine — that's investigation.
Writing SDD artifacts (proposals, designs, specs) is fine — that's capturing thinking.
Writing implementation code is not allowed.

## Approach

### Start with the user's question

Ask: what are you trying to figure out?

Common entry points:

- "I want to understand how X works before speccing it"
- "I'm not sure if this should be one change or two"
- "I need to figure out the right capability breakdown"

### Read existing context

Before forming opinions:

1. Check `.specs/specs/` for existing baseline specs
2. Check `.specs/changes/` for active changes
3. Read relevant code files if the user wants codebase investigation

### Thinking tools

Use freely:

- ASCII diagrams for architecture and flows
- Decision tables for tradeoffs
- Lists of forces for or against an approach
- Stakeholder maps, actor lists
- Numbered alternatives with tradeoffs

### Crystallization

When thinking becomes clear enough to act:

- Offer to create an artifact: "Want me to capture this as a proposal?" or "Should I sketch a design?"
- Route to the right skill: `sdd-propose`, `sdd-derive`, `sdd-translate`
- Don't force it — the user decides when thinking is done

## Output

No required output.
May produce:

- Notes, summaries, or decision records (in the conversation)
- SDD artifacts if the user decides to capture decisions (proposal.md, design.md)
- A recommendation for which SDD skill to run next

## Common Mistakes

- Writing implementation code (forbidden)
- Treating explore as a required step — it's optional, not a gate
- Forcing an artifact when the user just wants to think
- Not reading existing specs before forming opinions about the domain
