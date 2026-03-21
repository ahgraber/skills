---
name: sdd-verify
description: |-
  Use when verifying that an implementation matches a change's SDD artifacts. Triggers: "verify", "check implementation", "did I implement everything", "verify the change", "is implementation complete".
---

# SDD Verify

Verify implementation against change artifacts.
Produces a structured report across three dimensions with three severity levels.

## When to Use

- After completing some or all tasks — check coverage and correctness
- Before running `sdd-sync` — confirm implementation matches the change before syncing specs

## Soft Gate

If no tasks are marked complete in `tasks.md`, warn:

> "No completed tasks yet — verify output will be limited."

Offer to proceed anyway if the user wants early feedback.

## Verification Dimensions

| Dimension        | Question                   | What to check                                                  |
| ---------------- | -------------------------- | -------------------------------------------------------------- |
| **Completeness** | Is everything done?        | All tasks checked off, all delta spec requirements implemented |
| **Correctness**  | Is it implemented right?   | Implementation matches behavioral requirements in delta specs  |
| **Coherence**    | Does it follow the design? | Implementation follows decisions in design.md                  |

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

### Phase 4: Check Coherence

If `design.md` exists:

1. For each decision in `design.md`, verify the implementation follows it
2. Flag deviations as CRITICAL (contradicts explicit decision) or WARNING (diverges without documentation)

### Phase 5: Produce Report

```markdown
# Verification Report: {Change Name}

**Date:** {date} **Tasks:** {N}/{M} complete

## CRITICAL

- {Description of issue} — {file:line or area}

## WARNING

- {Description of issue}

## SUGGESTION

- {Description of improvement}

## Summary

{1-2 sentences on overall status and recommended next step}
```

If no issues found: "✓ Implementation matches all checked artifacts.
Ready for `sdd-sync`."

## Graceful Degradation

| Missing artifact | Behavior                                        |
| ---------------- | ----------------------------------------------- |
| `tasks.md`       | Skip completeness check, warn before proceeding |
| `design.md`      | Skip coherence check, note in report            |
| Delta specs      | Skip correctness check, note in report          |

"Warn before proceeding" means a conversational message to the user.
"Note in report" means adding a note inside the verification report itself.

## Common Mistakes

- Failing to read all artifacts before reporting
- Treating SUGGESTION-level issues as blockers
- Skipping graceful degradation — running verify is valid even with incomplete artifacts
- Not reading baseline specs for full behavioral context
