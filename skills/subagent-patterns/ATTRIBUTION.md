# Attributions and Citations

This file records external sources referenced while building or maintaining this skill.

## Methodology and patterns

- [obra/superpowers](https://github.com/obra/superpowers) by Jesse Vincent — source for the subagent-driven-development orchestrator model: file-based task briefs and reports, the durable progress ledger, `BASE..HEAD` (not `HEAD~1`) review packets, treating implementer reports as unverified claims, the no-pre-judging rule for reviewer prompts, and the mechanical/standard/frontier model tiers (accessed 2026-07-11)
- [mattpocock/skills](https://github.com/mattpocock/skills) by Matt Pocock — source for the thin-orchestrator / deep-discipline split, composing skills via prose invocation rather than cross-directory links, and running review lenses as parallel subagents so neither pollutes the other's context (accessed 2026-07-11)
- [Simon Willison — Subagents (Agentic Engineering Patterns)](https://simonwillison.net/guides/agentic-engineering-patterns/subagents/) — exploration/parallel/specialist subagent patterns, the context-preservation rationale, and the over-delegation caution (accessed 2026-07-11)
- [Anthropic — Subagents in Claude Code](https://claude.com/blog/subagents-in-claude-code) — context-isolation model, automatic vs. explicit delegation, and when-not-to-use guidance (accessed 2026-07-11)
- [OpenAI — Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) — parallel-spawn-then-collect model and read-heavy/parallel-friendly use-case framing (accessed 2026-07-11)

## Related skills in this repo

- `code-review` — the parallel-subagent reviewer templates (`references/parallel-subagent-review.md`) and the shared `build-review-packet.py`, reused by this skill's orchestrator review step rather than duplicated.
