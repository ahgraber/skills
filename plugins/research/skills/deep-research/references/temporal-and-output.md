# Temporal Relevance and Output Contract

## Temporal relevance

**Resolve the current date from context first, then anchor every query to it.**
Never hardcode a past year; read the year from context.
Choose the date granularity from what the user is actually asking for:

| User intent             | Granularity to encode | Example query phrasing                        |
| ----------------------- | --------------------- | --------------------------------------------- |
| "today", "right now"    | day                   | `<topic> 28 June 2026`, `<topic> today`       |
| "this week", "latest"   | week / recent days    | `<topic> this week`, `<topic> late June 2026` |
| "recently", "current"   | month                 | `<topic> June 2026`                           |
| "trends", "state of"    | year                  | `<topic> 2026`, `<topic> 2025 2026`           |
| historical / background | era or range          | `<topic> history`, `<topic> 2010-2020`        |

Rules:

- A year-only query silently buries anything recent — `<topic> 2026` will not return what shipped this morning.
  Match the granularity to what the question demands.
- Issue the same query in more than one date format — ISO (`2026-06-28`), long form
  (`28 June 2026`), and relative (`today`, `this week`) — because search backends index dates
  inconsistently.
- Record the chosen granularity in `topic-map.md` so every subagent inherits it.
- Capture each source's **publication date** and prefer recent sources for fast-moving topics;
  flag stale sources when recency matters.

## Output contract

The synthesizer reads the ledger, topic-map, and raw (invariant 4: never progress prose).
It calls no retrieval tools.
For any load-bearing or contested claim, it opens the raw pointer and confirms before writing.

### Principles

- **Lead with the spine.**
  The executive summary distills the through-line — the single argument, tension, or recurring frame running through the findings — not a reprise of the top hits.
  Distill in the summary; enumerate in the body.
- **Organize around findings and dimensions** — never as an annotated list of "what each source said."
- **Graded epistemics.**
  Label each claim's status: **established** (well-corroborated), **active debate** (sources disagree), or **speculation** (thin or projected).
  Carry confidence.
- **Conflicts side-by-side.**
  Disagreements appear with both positions and their verdicts — never silently collapsed.
- **Every claim is cited.**
  Inline source link for every non-obvious claim.
  Distinguish primary from secondary; flag single-origin claims.
- **State the limits.**
  An explicit gaps/limitations section, including whether the run stopped on **saturation** or hit the **budget cap** (say which — a capped run is not a complete one).

### Report skeleton

```markdown
# <Question>

_Researched <date> · temporal precision: <precision> · stopped on: <saturation|loop cap N>_

## Executive summary

The through-line in a sentence or two, then the headline answer and key findings with confidence levels.

## Findings by theme

### <Theme / dimension>

- Claim — [source](url) — _established_ (high confidence)
- Contested point:
  - Position A — [source](url) — _Supported_
  - Position B — [source](url) — _Partially supported_
  - Why they differ / which is stronger.

## Open debates and unresolved conflicts

Conflicts the evidence could not resolve, with both sides.

## Gaps and limitations

What was not covered, single-origin claims, stale sources, and whether the budget cap truncated the search.

## Sources

Numbered list of URLs with publication dates and primary/secondary tags.
```
