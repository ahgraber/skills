# Case File

Persistent agent-only working notes that fight cross-turn thread loss.

## Location

`$TMPDIR/brainstorming-<topic-slug>.md`.
Outside the project directory, not committed.

## Ownership

Agent-only.
Like Columbo's notebook.
Not narrated in chat.
Not dumped verbatim every turn.

## Schema

Five sections:

- `understood` — what's settled
- `open` — what's still being explored
- `discarded` — what was considered and rejected (and why)
- `tensions` — live contradictions or unresolved tradeoffs
- `engagement` — whether the user has materially engaged with each accepted point or just acquiesced (anti-sycophancy signal)

## Snapshot, not log

Old entries get refreshed in place.
No accumulated history.

## Write rhythm

Update after each substantive move (`reflect`, `diverge`, `lateral`, `steelman`, `name-tension`).
Skip updates on trivial turns.
Skip the case file entirely for sessions of ≤4 turns — overhead outweighs value.

## Read rhythm

Re-anchor at the start of each response in a long session.
Always re-read before invoking `name-tension` or `close`.

## Surface rules

- `name-tension` paraphrases from notes to cite the prior claim verbatim
- `close` consolidation uses notes as source material (written fresh, not dumped)
- If the user asks "where are we?"
  / "recap?"
  / "what have you got?"
  → summarize from notes in-chat
- User can request to see the file directly; otherwise it stays private

## Engagement section — anti-sycophancy use

When the user accepts a recommendation, log:

- The accepted point
- Whether the user materially engaged with the trade-offs (yes / no)
- If "no" twice in a row → trigger `name-tension` (self) probe, or restate the strongest counter before proceeding

This is the agent's calibration signal for whether agreements are signal or smoke.
Without it, agent-side sycophancy goes unobserved — by definition, the agent cannot detect its own sycophantic drift while in the same context that produced it.
