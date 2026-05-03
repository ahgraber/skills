---
name: evidence-rules
description: Shared evidence-classification contract for sdd-verify and its subagents — tiers, the SHALL-sufficiency rule, waivers, and citation format. Loaded by SKILL.md (orchestrator) and verify-subagent.md (subagents).
---

# Evidence Rules

Single source of truth for how `sdd-verify` classifies evidence and converts tier + RFC 2119 level into findings.
SKILL.md and `verify-subagent.md` both reference this file; do not duplicate the rules elsewhere.

## 1. Tiers

Every implemented requirement is classified by the strongest evidence available.

| Tier          | Meaning                                                                                                                                                                                                                      | Citation must name                                             |
| ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| **VERIFIED**  | Externally observable artifact you can re-inspect after the verify run — captured response body, generated schema file, command output, or an integration/e2e test that produced such an artifact and ran green this run.    | The specific output path or schema element.                    |
| **TESTED**    | A named, passing automated test from this verify run's test suite that exercises the requirement's behavior (typically unit-level). No external artifact, but the in-suite assertion is trusted because the suite ran green. | The specific test (`file::name` or framework equivalent).      |
| **INSPECTED** | No execution evidence exists — code may look right when read, but nothing demonstrates it.                                                                                                                                   | None — record `(no executable evidence)`.                      |
| **WAIVED**    | A `design.md` § Verification Waivers entry covers this requirement and provides a checkable manual evidence reference.                                                                                                       | The waiver entry + the manual evidence reference it points to. |

VERIFIED vs TESTED, in one line: **VERIFIED = an artifact survives the test run for re-inspection; TESTED = the assertion ran but left no inspectable artifact.**

## 2. Hard rule — Evidence sufficiency

Apply after assigning a tier:

| Level  | Tier                                               | Finding                                                                |
| ------ | -------------------------------------------------- | ---------------------------------------------------------------------- |
| SHALL  | INSPECTED                                          | **CRITICAL** — unless waived in `design.md` (then WAIVED, no finding). |
| SHALL  | WAIVED with no checkable manual evidence reference | **CRITICAL** — the waiver is itself invalid.                           |
| SHOULD | INSPECTED                                          | **WARNING**                                                            |
| MAY    | INSPECTED                                          | No automatic finding — MAY is optional.                                |
| any    | TESTED or VERIFIED                                 | No automatic finding from this rule — proceed to the contract check.   |

INSPECTED is never sufficient to clear a SHALL.
"I read the code and it looks right" is the absence of evidence, not evidence.
If runnable evidence does not exist, the gap is upstream — a test or schema check should have been a task in `tasks.md`.

## 3. Picking a tier — operational rules

1. **Prefer the strongest tier supported by real evidence.**
   If both a unit test (TESTED) and a schema diff (VERIFIED) cover the requirement, use VERIFIED and cite the schema.
2. **The cited evidence MUST exist and MUST have been executed in this verify run.**
   - If the cited test was deselected, skipped, or `xfail`'d, fall back to INSPECTED.
   - If a schema diff is empty when the requirement should produce one, fall back to INSPECTED.
   - If a captured output path does not exist, fall back to INSPECTED.
3. **"I read the code and it looks right" is INSPECTED.**
4. **Existence of code is not evidence.**
   A function that implements the requirement but is never called by any test or executed flow is INSPECTED.
5. **A tier without a checkable citation must drop to INSPECTED.**

## 4. Waivers

A requirement may be waived from the SHALL/INSPECTED → CRITICAL rule if `design.md` contains a `## Verification Waivers` section with this entry:

```markdown
## Verification Waivers

- **Requirement:** <requirement name or ID>
  **Reason:** <why automated execution evidence is not feasible — e.g., requires production data, third-party sandbox unavailable, manual operator step>
  **Manual evidence:** <path to captured output, runbook reference, screenshot, or commit where manual verification was recorded>
  **Recorded:** <commit SHA or ISO date when this waiver was added>
```

A waived requirement is reported under WAIVED in the report, not CRITICAL — but the manual evidence reference must be checkable.
A waiver without a checkable manual evidence reference is itself CRITICAL.

### Provenance check (anti-gaming)

The `Recorded` field exists to make it obvious when a waiver was added retroactively to clear a finding.
At verify time, the orchestrator MUST check whether the waiver entry predates the change branch.

**How to determine provenance:**

1. If `Recorded` is present, use it as an approximate indicator, but always confirm with git: `git log --follow -p design.md | grep -A4 "Requirement.*<name>"` or `git blame design.md`.
2. If `Recorded` is absent (waivers authored before this field was introduced), fall back to `git blame design.md` to determine when the line was last committed.

| Provenance                         | Treatment                                                                                                                                     |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| Waiver predates change branch      | Honor as WAIVED.                                                                                                                              |
| Waiver introduced in change branch | Surface as WAIVED but add **WARNING: waiver added during change implementation — confirm the manual evidence is independent of this change.** |

The orchestrator records this provenance call once and surfaces it in the report; subagents do not perform provenance checks.

## 5. Citation format

| Evidence type         | Citation form                                                                                                                                                                      |
| --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Unit/integration test | `path/to/test_file.py::TestClass::test_name` (or framework equivalent — Jest `describe > it`, Go `TestX/subtest`, etc.)                                                            |
| Captured output       | `<path provided by orchestrator>` plus the field/line to look for                                                                                                                  |
| Schema element        | `<schema path>#<JSON pointer>` — JSON pointers per RFC 6901 escape `/` as `~1` and `~` as `~0`. Example: `schemas/after/openapi.yaml#/paths/~1users` references the `/users` path. |
| Waiver                | `design.md § Verification Waivers → <requirement>`                                                                                                                                 |
