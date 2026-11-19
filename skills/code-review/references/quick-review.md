# Quick Review

A quick review is one agent reading the change, without partitions, subagents, or review state.
Run it only when the user asks for a "quick" or "sanity" check.
The report must say it is a quick review, not a standard or deep one.
Do not build partitions, hunt for more instances of a failure mode, or write review state.
Run the checks gate in `SKILL.md` Step 0 first: the hooks or linters and the test suite must pass, or the user must decide to review anyway.

## Triage

Build a short review plan before reading code in detail.

- Read the diff to understand what changed and why.
- For a medium or large change, or one that crosses modules, write a short plan focused on risk hotspots.
- For an unfamiliar codebase or a large diff, `references/git-diagnostics-before-review.md` has git commands for churn, bug clusters, contributor activity, and firefighting patterns in the files under review.

## Review (no edits)

For each changed file or module, summarize what changed and why.

Review tests before implementation: do tests exist for the changed behavior, do they assert behavior (not internals), do they cover edge cases and regressions?
For each test, ask what wrong implementation it would still accept; when you can, run a distinguishing input (probe scripts under `$TMPDIR` only, the project's own runner, no repository edits).
Test gaps shape what to scrutinize in the implementation pass.

Review the data structures before the logic.
A structure that can hold invalid states leaves each consumer to guard against them or assume them away, and both choices generate findings elsewhere in this review; correcting the shape retires them at the source.
Tests may pass either way, so make this a deliberate pass: `references/data-representation.md` has where to look, the three tests, and the evidence each finding must carry.

Then evaluate each area in this table.

| Area                        | Look for                                                                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Correctness & Logic         | Wrong behavior, broken contracts, off-by-one                                                                                 |
| Bugs & Edge Cases           | Nil/null paths, boundary values, error propagation                                                                           |
| Code Quality & Style        | Naming, readability, idiomatic usage                                                                                         |
| Structure & Maintainability | Coupling, duplication, separation of concerns                                                                                |
| Data Representation         | Structures that can hold invalid states, replicate information, or make every consumer enforce their rules                   |
| Best Practices              | Language/framework conventions, SOLID, DRY                                                                                   |
| Test Adequacy               | Wrong implementations the tests would still accept, missing tests for behavior changes, regression gaps                      |
| Performance                 | N+1 queries, unbounded loops/fan-out, missing pagination, sync calls in hot paths, large allocations, missed async           |
| Security & Risk             | OWASP Top 10: access control, injection, crypto, auth, supply chain, logging, error handling — use `securing-code` checklist |
| Documentation               | Misleading comments, missing doc for public API                                                                              |

Rules:

- If intent is unclear, ask clarifying questions before judging.
- If an area has no issues, state that explicitly.
- Reference specific code locations (line numbers or quoted snippets).
- Keep feedback actionable and concise.
- Review all changed lines before final judgment; open surrounding context where needed.
- Address runtime errors, validation, error handling, concurrency risks, resource usage, and obvious performance pitfalls.
- Behavior changes without tests → raise an issue (at least Medium).
- Style comments are non-blocking unless they map to project conventions.
- Dependency manifest or lockfile changes → assess supply-chain risk and compatibility.
- Call out TODO comments and their implications.
- For security & risk: use the `securing-code` skill's `references/tier2-review.md` checklist (OWASP-mapped) as the evaluation framework.
  When the `securing-code` skill is not installed, use the OWASP checklist in `assets/prompt-security-lens.md` instead.

## Findings

Compile findings into issues using the template in `assets/issue-template.md`.
Sort issues by priority: critical > high > medium > low.
For each issue, include blocking status, confidence, and evidence.
Use `Blocking: yes` only for a finding of critical or high priority that the diff introduced and that a real caller can reach, as in a standard or deep review (`review-dispatch.md`, "Synthesis").
Then report as `SKILL.md` Step 2 describes, without the review-state step, with each check from the gate and its result, and the user's reason for any check that failed.
