---
name: sdd-verify
description: |-
  Use when verifying that an implementation matches a change's SDD artifacts. Triggers: "verify", "check implementation", "did I implement everything", "verify the change", "is implementation complete", "check conformance", "validate schema changes".
---

# SDD Verify

Verify that the implementation satisfies the contracts stated in the change's specs.
Produces a structured report across four dimensions with three severity levels.

Specs are contracts — property statements about observable state (see `references/sdd-spec-formats.md` § 1).
Scenarios are evidence that samples those contracts, not the contracts themselves (§ 1.5).
`sdd-verify` samples: it checks that implementations honor the stated scenarios and traces through code for the broader contract claim.
It does not formally prove universal properties — strong claims supported by thin scenarios are a risk flag, not a failure.

> `SPECS_ROOT` is resolved by the `sdd` router before this skill runs.
> Replace `.specs/` with your project's actual specs root in all paths below.

## Invocation Notice

- Inform the user when this skill is being invoked by name: `sdd-verify`.

## When to Use

- After completing some or all tasks — check coverage and correctness
- Before running `sdd-sync` — confirm implementation matches the change before syncing specs

## Soft Gate

If no tasks are marked complete in `tasks.md`, warn:

> "No completed tasks yet — verify output will be limited."

Offer to proceed anyway if the user wants early feedback.

## Verification Dimensions

| Dimension        | Question                                           | What to check                                                                                        |
| ---------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Completeness** | Is everything done?                                | All tasks checked off, all delta spec requirements implemented                                       |
| **Contract**     | Does the implementation satisfy the spec contract? | Implementation honors each requirement's scenarios and the broader contract claim stated in the text |
| **Coverage**     | Do scenarios meaningfully sample the contract?     | Scenarios span happy path, boundaries, and plausible failure modes — not trivially-passing cases     |
| **Coherence**    | Does it follow the design?                         | Implementation follows decisions in design.md                                                        |
| **Conformance**  | Do schemas match the specs?                        | Generated schema diff confirms spec requirements are realized                                        |

## Severity Levels

| Level          | Meaning                                                              | Action required            |
| -------------- | -------------------------------------------------------------------- | -------------------------- |
| **CRITICAL**   | Implementation contradicts a requirement or design decision          | Must fix before proceeding |
| **WARNING**    | Implementation partially meets a requirement or deviates from design | Should address             |
| **SUGGESTION** | Minor improvement opportunity                                        | Optional                   |

## Process

### Phase 1: Load Artifacts

Read all available artifacts (graceful degradation — proceed with what exists):

- `.specs/changes/<name>/tasks.md` — task completion status
- `.specs/changes/<name>/design.md` — design decisions (if exists)
- `.specs/changes/<name>/specs/` — delta specs (if exist)
- `.specs/specs/` — baseline specs for full context

### Phase 2: Run Test Suite

Run the project's full test suite before any other checks.
Verification claims rest on observed behavior, so a green suite is the baseline evidence that the implementation actually works.

1. Run the project's standard test command (e.g., `pytest`, `npm test`, `cargo test`, the project's `nox`/`tox` session, or whatever the repo's contributor docs specify).
   Run the **full** suite — do not narrow to changed files or a single test path.
2. If any tests fail or error, flag each failure as CRITICAL in the report and stop further verification of the affected area until they are addressed.
   A failing suite invalidates Contract, Coverage, and Coherence conclusions.
3. If the project has no runnable test suite, note this in the report as a WARNING and continue.
4. Do not modify, skip, or `xfail` tests to make the suite pass — that is a CRITICAL finding, not a fix.

### Phase 3: Check Completeness

1. Count checked tasks vs. total tasks in `tasks.md`
2. For each delta spec requirement, verify a corresponding implementation exists in the codebase
3. Flag missing implementations as CRITICAL (SHALL requirement) or WARNING (SHOULD/MAY)

### Phase 4: Check Contract Satisfaction

Skip requirements already flagged as missing in Phase 3 — check contract satisfaction only for requirements that are implemented.

For each implemented requirement:

1. Read the requirement text — this is the **contract claim** (see `references/sdd-spec-formats.md` § 1).
2. Read the delta spec scenarios — these are concrete **evidence** sampling the claim.
3. Trace through the implementation to verify each scenario holds.
4. Consider whether the implementation honors the broader claim beyond the stated scenarios (e.g., if the requirement says "for any query satisfying C, the system SHALL return no relevant results," check that the implementation doesn't only work on the scenario examples).
5. Flag deviations as CRITICAL (contradicts requirement or scenario) or WARNING (partially meets it, or honors scenarios but appears to violate the broader claim).

### Phase 5: Check Scenario Coverage

For each requirement, assess whether its scenarios meaningfully sample the contract claim.
This is a coverage heuristic, not a formal check — it guards against requirements whose scenarios are too thin to catch a plausible failure.

Coverage smells to flag as WARNING:

- **Happy-path only** — every scenario's preconditions describe a well-formed, success-bound case.
  Missing boundary or adversarial cases.
- **No precondition variation** — all scenarios share essentially the same GIVEN.
  Fails to exercise different parts of the input space.
- **Scenarios restate the requirement** — the scenario adds no information beyond the requirement text (e.g., requirement: "user is authenticated"; scenario: "GIVEN valid credentials, WHEN submitted, THEN authenticated").
  No independent test value.
- **Universal claim, single scenario** — the requirement states a property over a class of inputs ("for any X", "whenever Y"), but only one scenario is provided.
  The claim is broader than the evidence.

Flag as SUGGESTION (not WARNING) if the requirement is narrow and a single scenario is adequate.

### Phase 6: Check Conformance (if schemas configured)

If `.specs/.sdd/schema-config.yaml` exists:

1. **Re-generate schema snapshots** — capture the current "after" state and store in `.specs/changes/<name>/schemas/after/`.
2. **Schema-vs-schema diff** (before → after) — what was added, modified, removed?
   Does this align with `schemas/expected.md` (if present)?
3. **Schema-vs-spec cross-check**:
   - ADDED requirements describing API or data shapes: does the schema confirm the change?
     Flag as CRITICAL if missing.
   - REMOVED requirements: is the corresponding schema element actually gone?
     Flag as WARNING if still present.
   - MODIFIED requirements: does the schema change match the new behavior?
4. **Drift detection** — schema changes with no corresponding spec requirement:
   - Flag as WARNING: "Schema shows new `<field/endpoint>` — not covered by any requirement"
5. **Authored schema check** — if the repo contains a committed authored schema, diff it against the newly generated snapshot:
   - Flag as WARNING if diverged: "Authored `<path>` differs from generated — may need updating"

If no schema config exists, skip silently.
Note in report if `schemas/expected.md` exists but extraction was not configured.

### Phase 7: Check Coherence

If `design.md` exists:

1. For each decision in `design.md`, verify the implementation follows it
2. Flag deviations as CRITICAL (contradicts explicit decision) or WARNING (diverges without documentation)

### Phase 8: Produce Report

```markdown
# Verification Report: {Change Name}

**Date:** {date} **Tasks:** {N}/{M} complete

## CRITICAL

- {Description of issue} — {file:line or area}

## WARNING

- {Description of issue}

## SUGGESTION

- {Description of improvement}

## CONFORMANCE

- [x] {What schema confirmed} — {requirement name}
- [ ] {What schema did not confirm} — {requirement name} (CRITICAL/WARNING)

## Summary

{1-2 sentences on overall status and recommended next step}
```

Omit empty sections (e.g., omit CONFORMANCE if no schema config exists).

If no issues found:

```text
All dimensions verified:
- [x] Completeness
- [x] Contract
- [x] Coverage
- [x] Coherence
- [x] Conformance (if applicable)

Ready for `sdd-sync`.
```

## Graceful Degradation

| Missing artifact      | Behavior                                                                  |
| --------------------- | ------------------------------------------------------------------------- |
| `tasks.md`            | Skip completeness check, warn before proceeding                           |
| `design.md`           | Skip coherence check, note in report                                      |
| Delta specs           | Skip contract and coverage checks, note in report                         |
| `schema-config.yaml`  | Skip conformance check, note in report                                    |
| `schemas/expected.md` | Skip expected-vs-actual diff within conformance; run drift detection only |

"Warn before proceeding" means a conversational message to the user.
"Note in report" means adding a note inside the verification report itself.

## Common Mistakes

- Failing to read all artifacts before reporting
- Skipping the full test suite, narrowing to changed files only, or trusting a prior local run instead of executing it now — verification rests on observed behavior, so the suite must run as part of this skill
- Treating SUGGESTION-level issues as blockers
- Skipping graceful degradation — running verify is valid even with incomplete artifacts
- Not reading baseline specs for full behavioral context
- Checking only that scenarios pass, not whether the implementation honors the broader contract claim (see `references/sdd-spec-formats.md` § 1.5 — scenarios are evidence, not definition)
- Accepting thin scenario coverage as sufficient — a universal claim with a single happy-path scenario should be flagged, not passed

## References

- `references/sdd-spec-formats.md` — contract shapes (§ 1.1), scenarios as evidence (§ 1.5)
- `references/sdd-schema.md` — schema evidence annotations (§ 1) and lifecycle policy (§ 4)
