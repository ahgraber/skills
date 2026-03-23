---
name: sdd-verify
description: |-
  Use when verifying that an implementation matches a change's SDD artifacts. Triggers: "verify", "check implementation", "did I implement everything", "verify the change", "is implementation complete", "check conformance", "validate schema changes".
---

# SDD Verify

Verify implementation against change artifacts.
Produces a structured report across four dimensions with three severity levels.

## When to Use

- After completing some or all tasks — check coverage and correctness
- Before running `sdd-sync` — confirm implementation matches the change before syncing specs

## Soft Gate

If no tasks are marked complete in `tasks.md`, warn:

> "No completed tasks yet — verify output will be limited."

Offer to proceed anyway if the user wants early feedback.

## Verification Dimensions

| Dimension        | Question                    | What to check                                                  |
| ---------------- | --------------------------- | -------------------------------------------------------------- |
| **Completeness** | Is everything done?         | All tasks checked off, all delta spec requirements implemented |
| **Correctness**  | Is it implemented right?    | Implementation matches behavioral requirements in delta specs  |
| **Coherence**    | Does it follow the design?  | Implementation follows decisions in design.md                  |
| **Conformance**  | Do schemas match the specs? | Generated schema diff confirms spec requirements are realized  |

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

### Phase 2: Check Completeness

1. Count checked tasks vs. total tasks in `tasks.md`
2. For each delta spec requirement, verify a corresponding implementation exists in the codebase
3. Flag missing implementations as CRITICAL (SHALL requirement) or WARNING (SHOULD/MAY)

### Phase 3: Check Correctness

Skip requirements already flagged as missing in Phase 2 — check correctness only for requirements that are implemented.

For each implemented requirement:

1. Read the delta spec scenario (GIVEN/WHEN/THEN)
2. Trace through the implementation to verify the scenario holds
3. Flag deviations as CRITICAL (contradicts requirement) or WARNING (partially meets it)

### Phase 4: Check Conformance (if schemas configured)

If `.sdd/schema-config.yaml` exists:

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

### Phase 5: Check Coherence

If `design.md` exists:

1. For each decision in `design.md`, verify the implementation follows it
2. Flag deviations as CRITICAL (contradicts explicit decision) or WARNING (diverges without documentation)

### Phase 6: Produce Report

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
- [x] Correctness
- [x] Coherence
- [x] Conformance (if applicable)

Ready for `sdd-sync`.
```

## Graceful Degradation

| Missing artifact      | Behavior                                                                  |
| --------------------- | ------------------------------------------------------------------------- |
| `tasks.md`            | Skip completeness check, warn before proceeding                           |
| `design.md`           | Skip coherence check, note in report                                      |
| Delta specs           | Skip correctness check, note in report                                    |
| `schema-config.yaml`  | Skip conformance check, note in report                                    |
| `schemas/expected.md` | Skip expected-vs-actual diff within conformance; run drift detection only |

"Warn before proceeding" means a conversational message to the user.
"Note in report" means adding a note inside the verification report itself.

## Common Mistakes

- Failing to read all artifacts before reporting
- Treating SUGGESTION-level issues as blockers
- Skipping graceful degradation — running verify is valid even with incomplete artifacts
- Not reading baseline specs for full behavioral context

## References

- `references/sdd-schema.md` — schema evidence annotations (§ 1) and lifecycle policy (§ 4)
