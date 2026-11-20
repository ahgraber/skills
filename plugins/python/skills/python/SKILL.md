---
name: python
description: |-
  Use when a Python change is about to be called done (before commit or PR) and whenever asked to review, audit, sanity-check, or clean up Python code or judge whether it meets standards. Also use at decision points the defaults cover: choosing retry/timeout/idempotency policy, config loading, pydantic placement, module boundaries, or a concurrency model.
---

# Python House Style Audit

## Overview

House style for Python, framed as an audit: rather than carrying a rulebook while writing code, sweep the target (a diff, file, package, or repo) for violations and report them.
The audit has two tiers: mechanical checks delegated to ruff, and judgment checks no linter can express.
Frontier coding agents already write reasonable Python, so the checks below are limited to the residual house preferences worth checking.

Every default below is a preferred starting point.
If a default conflicts with project constraints or worsens the outcome, follow the project and state the tradeoff and compensating controls (tests, observability, migration, rollback).

## When to Use

- A Python change is complete and about to be committed or shipped: audit the diff as part of wrapping up.
- Asked to review, audit, sanity-check, or clean up Python code, or whether it meets standards.
- Choosing among reliability, configuration, typing/validation, boundary, or concurrency approaches: the matching tier 2 section is the house default.
- Deciding which validation checks a Python change needs.
- A project has no lint policy and needs one bootstrapped (tier 1 carries the baseline).

### When NOT to Use

- Writing tests — use `writing-tests`; its `references/python-testing.md` carries the Python specifics.
- Notebook event-loop mechanics — use `python-notebooks-async`.
- Authoring demo or walkthrough notebooks — use `interactive-notebook-demo`.
- Merge-readiness verdicts on a diff — use `code-review`; this skill supplies the Python-specific lenses.

## Invocation Notice

- Tell the user when this skill is running: `python`.
  Skip the notice when the user asked for the skill by name or slash command; spelling and spacing need not match.
  A phrase from this skill's own trigger list is not a name — naming the work is not naming the skill.

## Shared Defaults

- Use the project-defined Python version.
- Use `uv` for environments and dependencies; run checks with `uv run ...`.
- Prefer `#%%` `.py` notebooks over `.ipynb` unless `.ipynb` is explicitly required.
- Local policy wins: repo config, linter rules, and project conventions override everything below.

## Tier 1 — Mechanical Audit (ruff)

> Last verified: 2026-08-18 — re-verify default-rule coverage and version notes against <https://docs.astral.sh/ruff/default-rules/> and the ruff changelog.

Run under the project's own configuration first:

```sh
uv run ruff check .
uv run ruff format --check .
```

- ruff >= 0.16 enables a broad default rule set (413 rules): bugbear, blind except, `try/except/pass`, naive datetimes, blocking calls and missing timeouts in async code, dangling `asyncio.create_task` references, unused async, and logging-call misuse are all machine-checked out of the box.
  Never hand-audit what ruff checks; run it and quote findings by rule ID.
- If the project pins an older ruff or restricts `select`, follow local policy; note the gap against the house baseline only when it is material to the change under review.
- When the project owns no lint policy, propose this starting point rather than imposing it:

```toml
[tool.ruff.lint]
extend-select = [
  "ANN2",  # missing return types on public functions
  "ASYNC", # async hygiene beyond the default subset
  "DTZ",   # full naive-datetime coverage
  "S113",  # requests calls without timeout
  "T20",   # stray print in library/service code
  "TRY",   # exception design (raise/except hygiene)
]
ignore = ["TRY003"] # long messages in raise — noisy in practice
```

- ruff >= 0.16 also formats Python code blocks inside Markdown and supports `ruff: ignore[rule-name]` suppression comments; prefer those over bare `noqa` codes in new suppressions.
- For dependency or lockfile changes, run the supply-chain audit scripts from the target project's root, passing each script by its full path in this skill's `scripts/`: `uv run pytest <path-to-this-skill>/scripts/test_uv_security_audit.py <path-to-this-skill>/scripts/test_pypi_security_audit.py -v`.
  Both warn (not fail) on findings; read the warnings.

## Tier 2 — Judgment Audit

Sweep the target for each finding class below.
These are not machine-checkable; report each finding with file:line and a concrete fix.
Each item names what to look for, why it is a problem, and the house default that resolves it.

### Boundaries and data flow

Before proposing a fix for a finding in this class, read `references/design-boundaries.md` for the reasoning behind these defaults and fuller guidance on fixes.

- Find I/O, environment reads, or clock and randomness calls inside core business logic.
  Effects buried in the core make the logic untestable without mocks and couple decisions to infrastructure.
  The default is Functional Core / Imperative Shell: the core computes decisions from its inputs, and the shell performs the effects.
- Find external input that reaches domain logic before validation.
  A check deep in the call stack runs after bad data has already spread.
  Validate and normalize at ingress so everything past the boundary can trust its inputs.
- Find ORM models, provider SDK types, or persistence schemas crossing module boundaries.
  Whatever crosses a boundary becomes a contract, and an internal type drags its whole schema with it.
  Share narrow DTO or value objects instead.
- Find transactions that span module boundaries.
  A shared transaction couples the modules' failure modes and creates rollback complexity nobody owns.
  Coordinate cross-module work through events or jobs, eventually consistent by default.
- Find speculative abstraction, deep inheritance, and `utils`/`common` dumping grounds.
  An abstraction built before the second concrete use is usually the wrong one, and a utils module is code nobody owns.
  Build the minimal golden path and prefer composition.

### Contracts and typing

Before proposing a fix for a finding in this class, read `references/design-boundaries.md` for the reasoning behind these defaults and fuller guidance on fixes.

- Find public functions that are untyped or typed `Any`.
  A public signature is the contract; without types, callers guess and refactors lose their safety net.
  Internal helpers do not need the same rigor.
- Find parameters typed more concretely than the function needs, and returns typed more loosely than what the function produces.
  Accept abstract interfaces (`Mapping`, `Sequence`, a `Protocol`) so callers are not forced into one container type; return concrete types so callers know what they hold.
- Find pydantic models threaded through internal data flow.
  Validation is a boundary activity; models everywhere add overhead and couple internals to the schema layer.
  Reserve pydantic for trust boundaries — API ingress, config, external data — and use the v2 APIs (`model_validate`, `model_dump`) in new code.
- Find public contract changes with no deprecation, versioning, or migration notes.
  Downstream consumers break silently.
  Prefer additive changes; an intentional break ships with a migration plan.

### Reliability policy

- Find outbound I/O without an explicit timeout, and long-running operations without a deadline.
  Library defaults are unbounded or arbitrary, so latency under failure becomes unpredictable.
  Set explicit timeouts on all external I/O, and pass an absolute deadline (`time.monotonic() + budget`) through nested calls instead of recomputing relative timeouts per layer.
- Find retries that are unbounded, stacked in more than one layer, or applied to permanent failures.
  Unbounded retries turn one outage into a retry storm; stacked layers multiply attempts; retrying a validation error only delays the real fix.
  Bound retries by attempt count and total deadline, back off exponentially with jitter, honor `Retry-After`, and keep retry logic in exactly one layer.
- Find retried writes with no idempotency guarantee.
  A retry after an ambiguous failure can apply the write twice.
  Use idempotency keys or a dedupe token, or disable automatic retry for that operation.
- Find retryability decided by matching exception message strings.
  Message text is not a contract and changes without warning.
  Encode retryability as policy data — an error kind and a `retryable` flag — with distinct terminal states for retryable and permanent outcomes.
- Find batch operations that report one opaque pass/fail.
  Callers cannot tell which items succeeded, so the only safe recovery is re-running everything.
  Return per-item outcomes unless all-or-nothing is the actual contract.

### Runtime and operations

- Find configuration read lazily at the point of use.
  A missing or malformed value then surfaces minutes or hours into a run instead of at startup.
  Load typed settings (for example `pydantic-settings`), validate them at startup, and keep imports free of configuration side effects.
- Find shutdown paths without signal handling, a bounded drain, or `try/finally` cleanup.
  An unhandled SIGTERM orphans subprocesses and half-written state; an unbounded drain turns a restart into a hung process.
  Handle termination signals, stop intake, drain in-flight work within a deadline, and clean up subprocesses, temp files, and handles in `try/finally`.
- Find jobs whose terminal states are implicit.
  When exhausted retries look like pending work, failures are invisible and queues silt up.
  Record retryable and permanent outcomes as distinct states, with an explicit dead-letter policy.
- Find failure logging that is unstructured or fires more than once per failure.
  Duplicate free-text logs cannot be counted, filtered, or correlated.
  Configure logging once at the entrypoint, use module loggers, log each failure once at a meaningful boundary with operation ID, phase, and attempt, and keep secrets out.
- Find health or readiness probes that return OK without checking dependencies.
  A probe that lies masks cascading failures from the orchestrator relying on it.

### Concurrency

- Find the concurrency model mismatched to the workload.
  Threads for I/O fan-out add synchronization bugs that asyncio avoids; asyncio adds nothing to CPU-bound work, which needs processes.
  Choose the model by workload, and reach for threads only with a stated reason.
- Find unbounded fan-out: `gather` or `submit` over an unbounded collection.
  Thousands of concurrent tasks starve the event loop or exhaust memory and file handles.
  Bound concurrency with a semaphore or queue.
- Find cancellation that stops the parent but not its children, or skips cleanup.
  Orphaned tasks hold connections open and leak until process exit.
  Propagate cancellation to child tasks and await their cleanup before re-raising.
- Find performance work with no before-and-after measurement.
  Unprofiled optimization solves the wrong problem, and its complexity stays.
  Measure first; re-measure to confirm the win.

### Tests

Python-specific testing practice is in `references/python-testing.md`.

- Find contract-asserted values with more than one write path and only the canonical path tested.
  A dedup shortcut or cache fast-path can silently drop what the contract requires.
  Each write-site needs its own test, and derived-field invariants need a test on the composed output.
- Find mock call-count assertions standing in for behavior assertions, patches applied at the definition site instead of the import location, and bare `Mock()` where autospec would catch signature drift.
  Each of these produces a test that passes while the behavior is wrong.
- Find bugfixes that land without a regression test that failed first.
  A test that never failed does not prove the bug is gone.

## Reporting

- Report tier 1 by running the commands and quoting output; report tier 2 findings with file:line, the default violated, and a proposed fix.
- Distinguish "violates a house default" from "violates this project's own convention"; the second outranks the first.
- Fix findings only on request or when the task is itself a cleanup; otherwise report.

## References

- `references/design-boundaries.md` — Functional Core / Imperative Shell, module ownership, boundary contracts, pydantic placement, contract evolution
- `references/python-testing.md` — Python-specific testing practices (also shared into `writing-tests`)
- `references/multi-python-testing.md` — version-matrix testing with nox + uv
