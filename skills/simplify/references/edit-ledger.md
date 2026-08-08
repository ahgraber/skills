# Edit Ledger

The ledger is the pass's report, persisted to a file.
It exists because the two questions a reader has about a cleanup land at different times: the diff answers _what changed_ now, and the ledger answers _why it was safe_ later — at review time, after the conversation is gone.
Deletions depend on it most: a diff can show removed lines but cannot carry the proof that nothing consumed them.

The ledger records one pass; it is not state that later passes read or update.
No skill is obligated to read an old ledger, entries have no status lifecycle, and nothing accumulates across passes.

## Location and lifetime

- Write to `.simplify/ledger-<YYYY-MM-DD-HHMM>.md` at the repo root.
- One file per pass; never overwrite an earlier one.
- The ledger is scratch, not source.
  Offer to keep it untracked: add `.simplify/` to the repo's root `.gitignore`, or create `.simplify/.gitignore` containing `*`.
- Tell the user the path when the pass finishes.

## Hard rules

- **Rationale lives here, not in the code.**
  When an edit needs explaining, the explanation goes in the ledger, never in a source comment narrating the pass.
- **Ledger IDs are ephemeral.**
  `A3`, `D2`, `T1` address entries within one file.
  They never appear in source, comments, commit messages, or PR descriptions.
- **Deferred entries are proposals.**
  Nothing in that section has been applied or approved.
- **Spec edits are never applied by a simplify pass.**
  They are recorded as suggestions and left for the user.

## Structure

```markdown
# Simplify Ledger — <YYYY-MM-DD HH:MM>

- Scope: <what was passed in: change set, file, dir, or repo>
- Lenses: <ids run>
- Verification: <ladder rung and command> — baseline <result>, final <result>
- Net: <n> files touched, <n> lines removed, <n> added

## Applied

| ID  | File:line         | Lens        | Change                         | Rationale                          |
| --- | ----------------- | ----------- | ------------------------------ | ---------------------------------- |
| A1  | `src/parse.py:88` | duplication | replaced with `text.strip_bom` | hand-rolled copy of shipped helper |

## Removed

One block per deletion.
Both proof answers are required; an entry missing either is incomplete.

### D1 — `src/legacy/shim.py` (entire file, 64 lines)

- **Consumers:** none.
  No callers or importers; no test asserts its behavior; textual sweep (config, entry points, fixtures, templates) found no reference; not a documented entry point.
- **History:** added to bridge the v1 config format; the v1 reader was deleted upstream, so the reason no longer applies.
- **Verified by:** full suite green after removal.

## Deferred

Proposals, in enough detail that a later executor — the `refactor` skill or anyone else — needs no other context.

### T1 — Decompose `Pipeline.run`

- **Files:** `src/pipeline.py` (+ estimated 6 call sites)
- **Why deferred:** restructures control flow; two existing tests assert on intermediate state and would need editing.
- **Proposed move:** extract the three stage bodies into private methods; `run` becomes sequencing only.
- **Blast radius:** ~180 lines moved, 2 tests rewritten, no public signature change.
- **Verification plan:** full suite green; `tests/test_pipeline.py` behavior assertions unchanged in meaning.

## Skipped

Findings not acted on, with the reason: false positives, out-of-scope pre-existing issues, or items routed to another skill.

| Finding                                | Why skipped                    |
| -------------------------------------- | ------------------------------ |
| `retry_count` shadows module constant  | pre-existing, outside scope    |

## Suggested spec changes — not applied

- `specs/ingest.md` §3 describes a `--legacy` flag removed in D1.
  Suggest striking the clause.
```

## Consumption by other skills

The `refactor` skill accepts a Deferred section as a work list when the user points it at one (or at the newest ledger).
If it executes a proposal, it appends an outcome block under that entry — what changed, files touched, verification result.
That append is a courtesy for the reader, not a protocol: refactor works equally well from proposals given in chat, and simplify never reads ledgers back.
