# Verification, Conflict, and Provenance

The review valve and the rules that make claims trustworthy.
The web gives no native provenance, so this layer is the skill's differentiator — none of the surveyed deep-research skills actually do it.

## When the valve fires

Once per round, at the converge moment — end of R3, and on new R4 material.
**Not per subagent.**
"Once per round" is a _cadence_; the valve itself **fans out by claim**.

## What to verify (scoped, not everything)

Verifying every claim is wasteful.
Verify a claim only if it is:

- **Load-bearing** — the report's conclusions depend on it.
- **Contested** — sources disagree, or the ledger has a `contested-on-its-face` tag.
- **Surprising** — counterintuitive, novel, or extraordinary.
- **Single-source** — only one source supports it (`single-source` tag).

Skip well-corroborated, mundane, background claims.
The `self-tag` column triages where to spend.

## How to verify (re-derive from raw)

1. Extract the atomic claims meeting the criteria above from the ledger.
2. Dispatch **one skeptic verifier per claim** (or small batch), in parallel.
3. Each verifier is told to **try to refute** the claim and to read the **raw tmpfile** at the claim's pointer — not the ledger summary, not a fresh search unless the raw is insufficient.
   Default to the more skeptical verdict when uncertain.
4. Record a verdict + confidence on the ledger row.

This is invariant 2 in action: the combine step (where the model is weakest) is re-grounded in source.
A verifier that only reads the distilled claim defeats the whole design.

## Verdict taxonomy

| Verdict                 | Meaning                                                                             |
| ----------------------- | ----------------------------------------------------------------------------------- |
| **Supported**           | Raw source directly and unambiguously supports the claim.                           |
| **Partially supported** | Supported with caveats, narrower scope, or weaker than stated.                      |
| **Unsupported**         | Raw does not support the claim (misread, overreach, or the source does not say it). |
| **Uncertain**           | Insufficient evidence either way.                                                   |

Hard rule: **a missing source is not a refuting source.**
Finding nothing on a claim means Uncertain; finding a source that says otherwise means Unsupported.
Do not conflate the two.

Never state a verdict without citing the specific raw pointer that grounds it.

## Evidence strength and independence

- Tag each supported claim with evidence strength: primary vs secondary source; direct
  measurement vs assertion; corroborated vs single-source.
- **Flag single-origin claims**: if every supporting source traces to one author, org, or study,
  mark it — multiple citations of one origin are not independent corroboration.
- Prefer **primary sources**.
  When a secondary source makes a claim, follow it to the primary and cite that.

## Conflict resolution — surface, don't collapse

When sources genuinely disagree:

1. **Present both positions side-by-side** with their evidence and verdicts.
   Do not silently pick a winner.
2. State **why** they differ when determinable: different dates, scopes, methods, definitions, or
   conflicts of interest.
3. If one position has materially stronger evidence, say so and why — but keep the other visible.
4. If the conflict cannot be resolved from available sources, mark it **Uncertain** and add it to
   the gaps/limitations section.

## Triggering R4

The valve sends the loop to R4 when it leaves **sufficient unresolved questions**:

- a load-bearing claim ended **Unsupported** or **Uncertain**, or
- a genuine conflict on a load-bearing point is unresolved, or
- the review exposed a **coverage gap** (a dimension never explored).

Contested-claim follow-ups are targeted re-fetches (re-review only the new material).
Coverage gaps loop back to R2 for the new dimension.
Both are bounded by the loop cap.
