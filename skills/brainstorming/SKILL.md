---
name: brainstorming
description: |-
  Use when turning a fuzzy idea into a refined design through dialogue — across software, writing, talks, events, naming, activities, or any creative/design task. Triggers: 'brainstorm', 'help me think about/through', 'figure out', 'work through', 'I have this idea', 'let's design', 'flesh this out'. Domain-agnostic. Not for: open-ended ideation with no anchor ('what should I build?'), implementing from a finalized spec, narrow binary decisions ('X or Y?'), retrospective review, mechanical refactors, or reframing whether the presenting question is the "real" one.
---

# Brainstorming

## Invocation Notice

Inform the user when this skill is being invoked by name: `brainstorming`.

## When to Use

- Fuzzy premise with an anchor (problem, audience, constraint) but no shape — "I need something for X but don't know [what shape/form it takes, how it works, how to implement it, what the right approach is]."
- Stuck direction: problem is clear, solution shape isn't
- Competing options: 2–3 candidate approaches; want pressure-testing
- Cross-domain design: software, writing, talks, events, naming, curricula
- Rubber-duck / organize own thinking (no decision required)

## When Not to Use

- Narrow binary decisions — just ask directly
- Retrospective review / postmortem
- Reframing whether the presenting question is the "real" question
- Implementing code from a finalized design — use the appropriate implementation skill
- Narrow bug fixes, mechanical refactors, formatting passes

## Core Discipline

The skill is a leash on the assistant's reflexes, not a ritual the user performs.
Three non-negotiables:

1. **HARD-GATE on artifacts and handoffs.**
   Verbal consolidation is not gated — when the user signals readiness, do it.
   Writing files, scaffolding code, producing spec files, or invoking another skill (e.g., `sdd-propose`, `handoff`) requires an explicit user request in the turn.
   **Not gated:** parallel-subagent dispatch within `lateral` or `steelman` — those are internal moves that return ideation material to this conversation, not handoffs to another skill.

2. **Narrate, don't gate.**
   Take the next move.
   In the same message, name the move in one short line, then do it.
   Do NOT ask permission between moves ("want me to X?") — it kills momentum and offloads pacing onto the user who came here because they didn't know where to go.
   The user redirects on the next turn ("back up", "wait, instead…", "no, push on X") — trust them to course-correct after seeing output, not before.
   Moves with user-visible cost (parallel-subagent dispatch in `lateral` or multi-steelman) get one-line narration before firing.
   The fire-conditions for those moves are the gate; if conditions aren't met, don't fire.

3. **Agent-paced, user-steerable.**
   The agent chooses the next move based on user signals.
   The user steers by dissent, not by picking from menus.
   When the user redirects, honor it without argument.

## Moves

The agent picks one move per turn.
Moves are cued inline (one line, then executed) — never announced as phase transitions.

| Move           | Trigger                                                                           | What it does                                                                                                                                                           |
| -------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `reflect`      | User is producing new material, exploring aloud, or has just answered             | Mirror back the shape ("sounds like you're partly deciding X and partly venting about Y")                                                                              |
| `diverge`      | Enough clarity to propose; user hasn't picked a direction                         | Offer 2–3 approaches that vary on the load-bearing axis. Lead with a recommendation; if user has expressed a lean, lead with the case for **not-X** first.             |
| `lateral`      | Option set looks homogeneous; user wants novelty; high-ambiguity domain           | Dispatch parallel persona subagents in isolated context for genuinely fresh angles. Narrate-then-dispatch when fire-conditions are met (see `references/lateral.md`).  |
| `steelman`     | A proposal is on the table; decision is substantive                               | Apply adversarial lenses (skeptic, adversary, future-self, audience, novice); produce a refined proposal. Cross-context for high-stakes. See `references/steelman.md`. |
| `name-tension` | A current claim conflicts with something stated earlier — by user **or by agent** | Flag the contradiction explicitly; cite the earlier claim. Includes self-tension (agent softening its own earlier sharper read).                                       |
| `close`        | User signals readiness or asks to wrap up                                         | Verbal consolidation: problem, approaches, direction, trade-offs, exclusions. **Not gated.** HARD-GATE engages only if user requests an artifact or skill handoff.     |

**Selecting the next move:** read the user's signals before acting.

- **First turn, terse anchor** (1–2 sentences, no elaboration) → `diverge`; don't stall on `reflect` fishing for more context.
- Long exploratory messages with new material → `reflect`.
- Enough clarity, no chosen direction → `diverge`.
- Option set in last `diverge` homogeneous **and** stakes justify dispatch, or user explicitly asks for lateral → `lateral`.
- A specific proposal is on the table → `steelman`.
- User revisiting territory you already covered → `name-tension` if there's a conflict, `reflect` otherwise.
- Agent's own current take softens an earlier sharper read → `name-tension` (self).
- User explicitly asks to wrap up → `close`.

## Case File

The agent maintains persistent agent-only working notes across turns to fight cross-turn thread loss.
Schema, write/read rhythms, and surface rules live in `references/case-file.md`.

Quick reference:

- **Location:** `$TMPDIR/brainstorming-<topic-slug>.md`
- **Sections:** `understood`, `open`, `discarded`, `tensions`, `engagement`
- **Snapshot, not log.**
  Refresh entries in place.
- **Read-anchor at the start of each response in long sessions.**
- **Always re-read before `name-tension` or `close`.**

## Anti-Drift Guardrails

These counter the assistant's default reflexes.

- **Resist reflexive clarification.**
  When you have enough to take a stab, take it.
  Do not ask "one more clarifying question" as comfort behavior.
- **Reflect when the user is producing.**
  Long user messages with new material → `reflect`, not fresh options.
  Don't pile structure on a flow that's still diverging.
- **Don't recap what you just did.**
  The user can read.
  Narrate the next move, not the last one.
- **Don't announce phases.**
  There are no phases.
  Moves are cued in one line and executed — never introduced as transitions between named sections.
- **Don't solicit permission between moves.**
  Narration is descriptive, not permissive.
  The user's standard redirection is always available.
- **Critique strength is not a function of user enthusiasm.**
  Form your assessment before checking the user's reaction.
  If you find yourself walking back a sharp earlier read because the user liked where you ended up, restore the read and surface the conflict via `name-tension` (self).
- **Lead against the lean.**
  When the user has expressed a preference, present the case for the opposite first.
  Forces real comparison instead of post-hoc justification.
- **Frictionless agreement is a smoke alarm.**
  Two consecutive low-engagement acknowledgements ("yeah", "sounds good", "ok") without engaging trade-offs → log to `engagement` in case file and probe the substance via `name-tension` (self) or restate the strongest counter.
- **Default LLM output is sharpened toward modal answers.**
  Persona dispatch alone doesn't fix that.
  When `lateral` runs, combine parallel subagents with verbalized sampling and selection-for-distance (see `references/lateral.md`).

## What This Skill Excludes

- Phase names and announced transitions
- Intent-routing at entry ("what do you want from this session?")
- Mode selection (full vs lightweight) at entry
- Mandatory spec files, commit steps, self-review, or user-review gates
- Implementation-skill handoff (`writing-plans`, `sdd-propose`, etc.) — the user chooses what (if anything) comes next
- Visual companion / browser-based mockups
- Narrow binary decisions, retroactive sense-making, presenting-vs-real-question reframing
- "Trade fours" or any move whose only job is to perform divergence — `lateral` (parallel subagents) is the divergence mechanism

## Terminal State

Verbal consolidation, in-conversation.
The user directs what (if anything) comes next.
No file is required.
No implementation skill is invoked.
If the user asks for a handoff, artifact, or next skill, honor the specific request — do not default to one.

## References

- `references/case-file.md` — schema, rhythms, surface rules
- `references/diverge.md` — batched mode, lead-against-lean, shape-distinct constraint
- `references/lateral.md` — parallel subagent dispatch, persona roster, anti-homogeneity tactics (verbalized sampling, MMR selection, persona distance), no-probabilities-to-user rule
- `references/steelman.md` — devil's advocate vs multi-steelman, cross-context dispatch, adversarial lenses, distinct-roster rule
