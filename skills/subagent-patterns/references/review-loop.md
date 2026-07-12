# Verification Loop

The coordinator verifies every unit of work before trusting it, then verifies the whole deliverable once at the end.
This is where the coordinator's judgment lives; do not delegate the arbitration.
The loop applies to any knowledge work a worker produces — code, a spec, a research report, a plan, a design doc, prose, an analysis — not only code.

> **Harness note.** `Agent` and `model` are example names for the dispatch tool and its per-dispatch model parameter; substitute your harness's equivalents.

## Scope the check to the delta, against the source of truth

Capture two things before you dispatch a verifier:

- **The delta** — what this worker actually produced (the new section, the changed files, the added findings), not the whole deliverable.
- **The source of truth** — what the delta is judged against: the brief, the spec, the question, the acceptance criteria.

Give the verifier both.
A verifier handed only the deliverable, with no source of truth, invents a standard and grades against it, then passes work that never met the real bar.

For **code**, the delta is the diff and the source of truth is the spec or plan; the `code-review` skill owns the mechanics (scoping the diff, `BASE..HEAD` not `HEAD~1`, the review packet, parallel review lenses).
For an **SDD change**, `sdd-verify` owns the whole verification: its dimensions, evidence tiers, severity, and gating.
When a purpose-built skill owns the check, use it instead of this loop and let its severity and gating win — `sdd-verify`, for one, treats a WARNING as advisory, not a blocker.

## Treat the report as unverified

The worker's report is a set of **claims**, not proof.

- A stated rationale never downgrades a finding.
  "I chose X because Y" does not make a defect not-a-defect.
- The worker's own success signal — tests pass, "I checked every source," "it matches the brief" — is itself a claim to check, not to accept.
  Warnings and hedges in what it produced are findings.

## Do not pre-judge the verifier

The point of a fresh-context verifier is independent judgment.
If your prompt says "don't flag X," "don't treat X as a defect," "at most minor," or "the plan chose X," stop: you are pre-rating findings and defeating the check.

Brief the verifier with the delta, the source of truth, the worker's report, and the constraints; then let it judge.
For code, reuse `code-review`'s reviewer templates (quality, spec-compliance, security, devil's-advocate).
One verifier at a peer tier suits a small unit; fan out for a large one.

## Severity → gating action

- **Critical / Important** — the unit can't be trusted until fixed.
  Run the fix loop below.
- **Minor** — note it for the final pass; don't block the unit on it.
- **"Can't verify from the delta alone"** — the verifier lacks cross-unit context you hold.
  Resolve it yourself: if it's a real gap, treat it as a failed check; if not, note why and move on.

## The fix loop

- A fix worker carries the same contract as the original: make the change, then produce evidence that it holds — re-run the tests for code, re-derive from the sources for research, re-check against the spec for a doc.
- Before re-dispatching the verifier, confirm the fix report contains that evidence, not just "fixed."
- Loop fix → verify until the unit is clean, then log it.

## Final pass over the whole deliverable

After every unit is clean:

1. Verify the whole deliverable once, on the most capable model.
   This is the one frontier judgment pass over how the units fit together.
2. If it returns findings, dispatch **one** fix worker with the complete list.
   One fixer per finding costs more than the work itself and loses cross-finding context.
3. Do the final read yourself.
   You are the last reviewer; the workers are inputs.

## Human arbitration

You escalate to the human; the workers never do (they can't see the user).

- Raise an important decision, a genuine ambiguity, or a case the source of truth doesn't cover **early**, before spending a dispatch on a guess.
- Assume the human has only a **cursory** understanding: no familiarity with the current unit, the context underlying the issue, or the option space.
  Give them that context and the options, framed as a decision, not a bare problem statement.
- You are the final arbiter of the verifier's findings: accept, downgrade with rationale, or escalate the ones that hinge on intent you can't confirm.
