---
name: sdd-verify
description: |-
  Use when verifying that an implementation matches a change's SDD artifacts. Triggers: "verify", "check implementation", "did I implement everything", "verify the change", "is implementation complete", "check conformance".
---

# SDD Verify

Verify that the implementation satisfies the contracts stated in the change's specs.
Produces a structured report across **five** dimensions (Completeness, Contract, Coverage, Coherence, Conformance) with three severity levels.

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

## When Not to Use

- No active change exists (`.specs/changes/<name>/` is missing) — the skill is change-scoped; use `sdd-derive` to retrofit specs from existing code instead
- Schema-only validation with no spec context — run the project's schema generation directly and diff
- During implementation itself — use `sdd-apply` to drive work; verify after

## Soft Gate

Before starting, check `.specs/changes/<name>/tasks.md`:

- If `tasks.md` is missing, warn: "No `tasks.md` for this change — completeness check will be skipped."
  Offer to proceed anyway.
- If `tasks.md` exists but no tasks are marked complete, warn: "No completed tasks yet — verify output will be limited."
  Offer to proceed anyway.

## Verification Dimensions

| Dimension        | Question                                           | What to check                                                                                        |
| ---------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Completeness** | Is everything done?                                | All tasks checked off, all delta spec requirements implemented                                       |
| **Contract**     | Does the implementation satisfy the spec contract? | Implementation honors each requirement's scenarios and the broader contract claim stated in the text |
| **Coverage**     | Do scenarios meaningfully sample the contract?     | Scenarios span happy path, boundaries, and plausible failure modes — not trivially-passing cases     |
| **Coherence**    | Does it follow the design?                         | Implementation follows decisions in `design.md`                                                      |
| **Conformance**  | Do schemas match the specs?                        | Generated schema diff confirms spec requirements are reflected in the schema                         |

## Severity Levels

| Level          | Meaning                                                              | Action required            |
| -------------- | -------------------------------------------------------------------- | -------------------------- |
| **CRITICAL**   | Implementation contradicts a requirement or design decision          | Must fix before proceeding |
| **WARNING**    | Implementation partially meets a requirement or deviates from design | Should address             |
| **SUGGESTION** | Minor improvement opportunity                                        | Optional                   |

Severity is not the same thing as sync gating.
A finding can keep its original severity and still be non-blocking when the user explicitly authorizes that exception and it is recorded per `references/sdd-change-formats.md`.

## Evidence Rules

Evidence classification (VERIFIED / TESTED / INSPECTED / WAIVED), the SHALL/INSPECTED → CRITICAL sufficiency rule, the waiver format and provenance check, and the citation format are defined in `references/evidence-rules.md`.
**Read that file before Phase 4** — both the orchestrator and any subagents need it.

In summary:

- **VERIFIED** — externally observable artifact you can re-inspect after the run (response body, schema file, captured output).
- **TESTED** — named, passing automated test from this verify run's suite.
- **INSPECTED** — no execution evidence; static reading only.
- **WAIVED** — `design.md` § Verification Waivers entry with checkable manual evidence.

Hard rule: **SHALL at INSPECTED → CRITICAL** unless waived.
Static reading is never sufficient for a SHALL.

Verification overrides are separate from waivers:

- **Waiver** — evidence exception for a requirement with manual evidence.
- **Override** — audit-tracked permission to proceed despite a known blocking finding or gate outcome.

Overrides never change severity; they only affect blocking status.
Use them to preserve decision continuity, not to erase or reclassify findings.

## Parallel Subagent Path

Phases 4–6 (Evidence, Contract, Coverage) SHALL be evaluated against the parallel-subagent gate before Phase 3 begins.
Single-agent execution is permitted only when the gate routes you there — it is not the default.

The gate evaluation is a numbered phase step (see **Phase 2.5**).
The full availability gate, granularity proposal, model resolution, dispatch protocol, and synthesis steps live in `references/parallel-subagent-path.md`.

## Process

### Phase 1: Load Artifacts

Read all available artifacts (graceful degradation — proceed with what exists):

- `.specs/changes/<name>/tasks.md` — task completion status
- `.specs/changes/<name>/design.md` — design decisions and any `## Verification Waivers` / `## Verification Overrides` (if exists)
- `.specs/changes/<name>/specs/` — delta specs (if exist)
- `.specs/specs/` — baseline specs for full context

### Phase 2: Run Test Suite and Capture Results

Run the project's full test suite before any other checks.
Verification claims rest on observed behavior, so a green suite is the baseline evidence that the implementation actually works.

1. **Discover the test command** by checking, in order:

   - Project contributor docs: `CONTRIBUTING.md`, `README.md`, `AGENTS.md`, `CLAUDE.md`.
   - Build manifests: `Makefile` targets, `package.json` `scripts.test`, `pyproject.toml` `[tool.pytest.ini_options]` or `[tool.poetry.scripts]`, `tox.ini`, `noxfile.py`, `Cargo.toml`.
   - CI config: `.github/workflows/*test*.yml`, `.gitlab-ci.yml`.
   - If still ambiguous, ask the user once and remember the answer for the rest of the run.

2. **Run the full suite with per-test-ID output** — do not narrow to changed files or a single test path.
   Subagents confirm citations by searching the log for individual test names, so the output must show each test's pass/fail status by name.
   Common flags: `pytest -v`, `jest --verbose`, `go test -v`, `nox -- -v`.
   For machine-readable output use `pytest --junit-xml=<path>` and point subagents at the XML.
   If the runner cannot produce per-test-ID output, treat all requirements as INSPECTED and note this as a WARNING.
   Capture the output to `.specs/changes/<name>/.verify/test-output.log`.

3. **If any tests fail or error**, flag each failure as CRITICAL in the report and **stop the verify run by default** — do not proceed to later phases.
   A failing suite invalidates Contract, Coverage, and Coherence conclusions, and there is no reliable way to localize "affected area" without a test→requirement map.
   Re-run after fixes.

   If the user explicitly says they already know about the failing suite and wants to proceed anyway, continue only in a **failing-suite override** mode:

   - Keep every test failure at its original severity in the report.
   - Record that the remaining phases are diagnostic only, not a clean verification pass.
   - Before recommending `sdd-sync`, record the exception per `references/sdd-change-formats.md` and ensure `tasks.md` contains an unchecked remediation task.
   - Never conclude "all applicable dimensions verified" or otherwise present the run as fully passing.
   - The parallel-subagent gate (Phase 2.5) handles whether subagent dispatch is allowed under override; do not decide that here.

4. **If the project has no runnable test suite**, note this as a WARNING and continue — every requirement will land at INSPECTED at best.

5. **Do not modify, skip, or `xfail` tests to make the suite pass** — that is itself a CRITICAL finding.

### Phase 2.5: Evaluate Parallel-Subagent Gate

You SHALL run this gate after Phase 2 and before Phase 3.
Single-agent execution is allowed only when the gate routes you there.

Checklist — do all four:

1. **Read** `references/parallel-subagent-path.md` § 1 (Availability Gate) and § 2 (Granularity).

2. **Count** delta spec requirements across all in-scope capabilities.

3. **Apply** the gate table in § 1 (first match wins) to determine the path.

4. **Announce** the outcome to the user using this template, then wait for confirmation if parallel:

   ```text
   Parallel gate: <N> requirements across <K> capabilities.
   Path: <single-agent | parallel> — <reason from gate table row>.
   <If parallel:> Proposing <P> subagents at <per-capability | per-requirement> granularity. Confirm or override.
   ```

If the gate sends you to single-agent, proceed to Phase 3 yourself.
If the gate sends you to parallel, wait for user confirmation, then resolve model and dispatch per `references/parallel-subagent-path.md` §§ 3–4.

**Failing-suite override and the gate.**
The gate table in `references/parallel-subagent-path.md` § 1 already partitions failing-suite states (rows 2 and 3): parallel dispatch is allowed under override only when the dispatch inputs explicitly carry the override state and the known overridden blockers; otherwise the gate routes to single-agent.
Apply that table — do not improvise a separate decision here.

**Audit rule.**
If no gate-outcome announcement appears in the run, the gate was not evaluated and the next phase must not begin.

### Phase 3: Generate Schema Snapshot (if schemas configured)

If `.specs/.sdd/schema-config.yaml` exists, regenerate "after" snapshots **now**, before evidence classification, so the schema diff is available as VERIFIED evidence in Phase 4.

1. Generate snapshots into `.specs/changes/<name>/schemas/after/`.
2. Compute the before→after diff and store the diff path for Phase 4 and Phase 7 to consume.

If no schema config exists, skip silently.
Phase 7 is where the diff is interpreted against the spec; this phase only produces the artifact.

### Phase 4: Check Completeness and Evidence

This is the first per-requirement phase — eligible for subagent dispatch (see `references/parallel-subagent-path.md`).

1. Count checked tasks vs. total tasks in `tasks.md`.
2. For each delta spec requirement, verify a corresponding implementation exists in the codebase.
   Flag missing implementations as CRITICAL (SHALL) or WARNING (SHOULD/MAY).
3. For each implemented requirement, identify and **cite** the strongest available evidence per `references/evidence-rules.md` §§ 1, 3, 5:
   - **VERIFIED** — name the integration/e2e test that ran in Phase 2 with its captured output, the schema diff from Phase 3, or the captured command output.
   - **TESTED** — name the unit-level test from Phase 2 that exercises the requirement.
   - **INSPECTED** — record this only when no executable evidence exists.
4. Apply the **Evidence sufficiency rule** (`evidence-rules.md` § 2):
   - SHALL at INSPECTED → CRITICAL, unless waived in `design.md` (then WAIVED, subject to the provenance check in § 4).
   - SHOULD at INSPECTED → WARNING.
   - MAY at INSPECTED → no automatic finding.
5. If a citation cannot be resolved (named test does not exist in the captured Phase 2 output, output path is missing, schema diff is empty when one was expected), the requirement falls back to INSPECTED.

If Phase 2 is in failing-suite override mode, passing tests from that run may still be cited for requirement-local evidence, but the report must state that the overall suite is failing and that downstream conclusions are advisory.

The output of this phase is a per-requirement evidence table that drives Phase 5 and the final report.
On the parallel path, the orchestrator assembles this table from subagent findings during synthesis.

### Phase 5: Check Contract Satisfaction

Skip requirements flagged as missing in Phase 4.
For each requirement at TESTED or VERIFIED tier, confirm the cited evidence actually demonstrates the contract claim — do not just trust the test name.
INSPECTED-tier requirements are not contract-checked here; their tier already determined the finding in Phase 4.

If Phase 2 is in failing-suite override mode, Contract findings are still useful for triage, but they do not clear the change for release or sync.

For each implemented requirement at TESTED or VERIFIED:

1. Read the requirement text — this is the **contract claim** (`references/sdd-spec-formats.md` § 1).
2. Read the delta spec scenarios — concrete **evidence** sampling the claim.
3. Inspect the cited test or output to verify each scenario holds in the executed evidence (not just in the source code).
4. Consider whether the implementation honors the broader claim beyond the stated scenarios (e.g., if the requirement says "for any query satisfying C, the system SHALL return no relevant results," check that the implementation doesn't only work on the scenario examples).
5. Flag deviations as CRITICAL (contradicts requirement or scenario) or WARNING (partially meets it, or honors scenarios but appears to violate the broader claim).

### Phase 6: Check Scenario Coverage

For each requirement, assess whether its scenarios meaningfully sample the contract claim.
This is a coverage heuristic, not a formal check — it guards against requirements whose scenarios are too thin to catch a plausible failure.

If Phase 2 is in failing-suite override mode, label Coverage conclusions as provisional because the suite is already known red.

Coverage smells to flag as WARNING:

- **Happy-path only** — every scenario describes a well-formed, success-bound case.
  Missing boundary or adversarial cases.
- **No precondition variation** — all scenarios share essentially the same GIVEN.
  Fails to exercise different parts of the input space.
- **Scenarios restate the requirement** — the scenario adds no information beyond the requirement text.
  No independent test value.
- **Universal claim, single scenario** — the requirement states a property over a class of inputs ("for any X", "whenever Y"), but only one scenario is provided.

Flag as SUGGESTION (not WARNING) if the requirement is genuinely narrow and a single scenario is adequate (e.g., "the response Content-Type SHALL be `application/json`").

### Phase 7: Check Conformance (if schemas configured)

If Phase 3 produced a schema diff:

1. **Schema-vs-schema diff** (before → after) — what was added, modified, removed?
   Does this align with `schemas/expected.md` (if present)?
2. **Schema-vs-spec cross-check**:
   - ADDED requirements describing API or data shapes: does the schema confirm the change?
     Flag as CRITICAL if missing.
   - REMOVED requirements: is the corresponding schema element actually gone?
     Flag as WARNING if still present.
   - MODIFIED requirements: does the schema change match the new behavior?
3. **Drift detection** — schema changes with no corresponding spec requirement: flag as WARNING ("Schema shows new `<field/endpoint>` — not covered by any requirement").
4. **Authored schema check** — if the repo contains a committed authored schema (e.g., a hand-maintained `openapi.yaml`), diff it against the newly generated snapshot.
   Flag genuine divergences as WARNING; tolerate documented additions (e.g., vendor extensions, computed fields) noted in `design.md`.

If `schemas/expected.md` exists but Phase 3 was skipped (no `schema-config.yaml`), note this in the report — the user expected schema tracking but it was not configured.

### Phase 8: Check Coherence

If `design.md` exists:

1. For each decision in `design.md`, verify the implementation follows it via static reading.
2. Flag deviations as CRITICAL (contradicts an explicit decision) or WARNING (diverges without documentation).

If Phase 2 is in failing-suite override mode, Coherence findings remain worth reporting, but they do not outweigh the CRITICAL failing-suite status.

Coherence findings are static reads by design — `design.md` records HOW choices, not external contracts, so the evidence-tier rule does not apply here.
A decision either is or is not reflected in code; if the decision needs runtime confirmation, it should have been promoted to a spec requirement.

### Phase 9: Produce Report

Before writing the Summary, classify blocking status:

- Any finding or gate outcome the skill says "must fix before proceeding," "stop," or "blocked" is **blocking** by default.
- A blocking finding or gate outcome becomes **non-blocking for sync** only when a matching override is recorded per `references/sdd-change-formats.md`.
- Chat-only instructions are not sufficient once the report is finalized; the override must be written into the change artifacts.

For each entry in `design.md § Verification Overrides`, carry the audit record into the report:

- Echo the finding, stage, reason, constraints, follow-up task, approved-by value, and recorded value.
- If this verify run is proceeding under an override, the Summary must make that intervention explicit so later stages can recover the decision context without rereading the whole conversation.

```markdown
# Verification Report: {Change Name}

**Date:** {date} **Tasks:** {N}/{M} complete

## Evidence

| Requirement | Level (SHALL/SHOULD/MAY) | Tier (VERIFIED/TESTED/INSPECTED/WAIVED) | Citation                                   |
| ----------- | ------------------------ | --------------------------------------- | ------------------------------------------ |
| {name}      | SHALL                    | TESTED                                  | `tests/path::test_name`                    |
| {name}      | SHALL                    | WAIVED                                  | design.md § Verification Waivers → {ref}   |
| {name}      | SHOULD                   | INSPECTED                               | (no executable evidence — flagged WARNING) |

## CRITICAL

- {Description of issue} — {file:line or area}

## WARNING

- {Description of issue}

## SUGGESTION

- {Description of improvement}

## WAIVED

- {Requirement} — manual evidence: {reference} (per design.md § Verification Waivers; provenance: {predates change | added during implementation | added after verify failure})

## OVERRIDES

- {blocking finding or gate outcome} — stage: {stage}; reason: {reason}; constraints: {constraints}; follow-up: {tasks.md task text}; approved by: {approved by}; recorded: {recorded}

## CONFORMANCE

- [x] {What schema confirmed} — {requirement name}
- [ ] {What schema did not confirm} — {requirement name} (CRITICAL/WARNING)

## Summary

{1-2 sentences on overall status and recommended next step}
```

Omit empty sections (e.g., omit CONFORMANCE if no schema config exists; omit WAIVED if no waivers apply).

If Phase 2 proceeded under a failing-suite override, the Summary must say so explicitly and recommend fixing or isolating the failing tests before treating the verify run as complete.
If any blocking findings are overridden for sync, the Summary must say that the run is not a clean pass and that `sdd-sync` is permitted only under the recorded overrides.

If no issues found:

```text
All applicable dimensions verified:
- [x] Completeness
- [x] Contract
- [x] Coverage
- [x] Coherence (if design.md exists)
- [x] Conformance (if schema-config.yaml exists)
- [x] Evidence — every SHALL at TESTED or VERIFIED (or WAIVED with checkable manual evidence)

Ready for `sdd-sync`.
```

Only include checklist items for dimensions that actually applied — match what's in the report.

If the run has no remaining blockers but does include overrides, do not use the clean-pass template above.
State instead that verification found issues the user explicitly chose not to let block sync, and that remediation remains open in `tasks.md`.

## Graceful Degradation

| Missing artifact      | Behavior                                                                  |
| --------------------- | ------------------------------------------------------------------------- |
| `tasks.md`            | Skip completeness check, warn before proceeding                           |
| `design.md`           | Skip coherence check and waiver lookups, note in report                   |
| Delta specs           | Skip contract and coverage checks, note in report                         |
| `schema-config.yaml`  | Skip Phase 3 snapshot and Phase 7 conformance check, note in report       |
| `schemas/expected.md` | Skip expected-vs-actual diff within conformance; run drift detection only |

"Warn before proceeding" means a conversational message to the user.
"Note in report" means adding a note inside the verification report itself.

## Common Mistakes

- Skipping the full test suite, narrowing to changed files only, or trusting a prior local run instead of executing it now — verification rests on observed behavior, so the suite must run as part of this skill.
- Not capturing test output to disk in Phase 2 — without the captured log, evidence citations have nothing to point at.
- Treating SUGGESTION-level issues as blockers, or treating coverage smells as CRITICAL.
- Skipping graceful degradation — running verify is valid even with incomplete artifacts.
- Not reading baseline specs for full behavioral context.
- Checking only that scenarios pass, not whether the implementation honors the broader contract claim (`references/sdd-spec-formats.md` § 1.5 — scenarios are evidence, not definition).
- Marking a requirement VERIFIED or TESTED without a checkable citation, or accepting a waiver without checkable manual evidence — both fall back to INSPECTED / CRITICAL per `evidence-rules.md`.
- Skipping the waiver provenance check (`evidence-rules.md` § 4) — waivers added in the same branch as the implementation, especially after a failed verify, need to be surfaced.
- Recording an override in `design.md` but failing to carry its context into the OVERRIDES section or Summary, which breaks the audit trail for later verify/sync work.
- Treating an override as a severity downgrade, or honoring a chat-only override without recording it in `design.md` and `tasks.md`.
- Proceeding to Phase 3 without evaluating the parallel-subagent gate (Phase 2.5) — the gate is mandatory; if no gate-outcome announcement appears in the run, you skipped it.
  Single-agent execution is a gate result, not a default.
- On the parallel path: re-running per-requirement phases on the orchestrator, mixing granularities, dispatching above the concurrency cap, or silently defaulting the model — see `references/parallel-subagent-path.md` § 6.

## References

- `references/evidence-rules.md` — tiers, sufficiency rule, waivers, provenance check, citation format
- `references/parallel-subagent-path.md` — availability gate, granularity, dispatch, synthesis
- `references/verify-subagent.md` — canonical job description for subagents on the parallel path
- `references/sdd-spec-formats.md` — contract shapes (§ 1.1), scenarios as evidence (§ 1.5)
- `references/sdd-schema.md` — schema evidence annotations (§ 1) and lifecycle policy (§ 4)
