---
name: python
description: Use when planning, implementing, or reviewing Python feature, bugfix, integration, or performance changes and you need consistent standards for architecture, typing, reliability, testing, and operations with uv, ruff, pytest, and pydantic boundaries.
---

# Python Contributor Guide

## Purpose

Use this skill as preferred default guidance for planning, implementing, and reviewing Python changes with consistent engineering standards.
It is for contributors doing new features, bugfixes, integrations, refactors, and performance work.

This guide does not prescribe product-specific business logic or framework-specific architecture.
If repo conventions conflict with this guide, follow the repo and ask targeted clarifying questions before coding.

## How To Use This Guide

1. Start with the chapter matching your task.
2. Apply `Project Defaults` and `Definition of Done` as the baseline for every change.
3. Read only the chapter reference files listed in this guide.
4. Pull additional chapter references only when your change crosses concerns.
5. If you choose a non-default approach, document why it fits the case better and what guardrails mitigate risk.

### Quick Task Routes

- New feature: `Code Design & Readability` -> `Types & Public Interfaces` -> `Data & State` -> `Testing` -> `Operations`
- Bugfix: `Errors & Reliability` -> `Testing` -> `Definition of Done`
- Integration work: `External Integrations & Resilience` -> `Errors & Reliability` -> `Testing` -> `Operations`
- Performance work: `Concurrency & Performance` -> `Testing` -> `Operations`

## Default-First, Context-Aware Decisions

- Treat this guide and its references as preferred defaults for common Python work, not universal rules.
- If a default conflicts with repo constraints, platform/runtime realities, compatibility requirements, or delivery risk, avoid force-fitting it.
- In those cases, suggest one or more alternatives and explain why they are a better fit for this specific change.
- When deviating, state tradeoffs and compensating controls (tests, observability, migration/rollback plan).

## Project Defaults (Preferred Baseline)

- Python runtime:
  - Use project-defined Python version first.
  - If unspecified, prefer modern Python 3.11+ conventions.
- Environment and dependencies:
  - Use `uv` for environments, dependency management, and script execution.
- Lint and format:
  - Use `ruff check` and `ruff format`.
- Tests:
  - Use `pytest` for unit and integration testing.
- Notebook files:
  - Prefer `#%%`-formatted `.py` notebooks over `.ipynb` unless `.ipynb` is explicitly requested.
- Data boundaries:
  - Use pydantic/pydantic-settings for external input, config, and serialization boundaries.
  - Keep pure domain logic on plain Python types when validation frameworks are unnecessary.

## Definition of Done

Before merge, ensure:

- Behavior is correct for happy path, failure modes, and edge cases.
- New or changed behavior has tests, including regression coverage for bugfixes.
- Public interfaces are typed and contracts are explicit.
- Error handling and reliability policy are explicit (timeouts, retries, idempotency where relevant).
- Operational needs are handled (logs, config, graceful runtime behavior).
- Documentation is updated when contracts or user-visible behavior change.

## Table of Contents

1. Setup & Workflow
2. Code Design & Readability
3. Types & Public Interfaces
4. Errors & Reliability
5. Testing
6. Data & State
7. Concurrency & Performance
8. External Integrations & Resilience
9. Operations (Services/Jobs/CLI)

## 1) Setup & Workflow

- Keep a repeatable local flow that mirrors CI checks.
- Use `uv`-managed environments and run checks with project-scoped tooling.
- Before PR updates, run `uv run ruff check .`, `uv run ruff format --check .`, and `uv run pytest`.
- Keep branches and commits small, reviewable, and reversible.
- Separate behavior changes from broad refactors where possible.

Deep guidance:
- `references/workflow.md`
- `references/branch-commit-scope.md`

## 2) Code Design & Readability

- Prefer readability-first design: explicit control flow, explicit data movement, and names that reflect domain intent.
- Bias toward minimal golden-path code; add defensive branches only when tests or operating history justify them.
- Keep strict module boundaries: each module owns its invariants and exposes explicit interfaces.
- Use composition by default and inheritance only when subtype substitution materially improves the interface.
- Apply Functional Core / Imperative Shell inside each module: core decides, shell orchestrates side effects.

Deep guidance:
- `references/design-rules.md`
- `references/readability-and-complexity.md`
- `references/module-boundaries.md`
- `references/functional-core-shell.md`
- `references/refactor-guidelines.md`

## 3) Types & Public Interfaces

- Treat type hints as interface design, not decoration.
- Type public APIs and keep contracts explicit and stable.
- Use `Protocol` and narrow interfaces at boundaries.
- Use pydantic models at trust boundaries, not everywhere by default.

Deep guidance:
- `references/typing-policy.md`
- `references/contract-evolution.md`
- `references/pydantic-boundaries.md`

## 4) Errors & Reliability

- Design errors for caller action and debugging context.
- Preserve cause chains at boundaries with explicit translation.
- Catch only what you can handle and avoid silent failure paths.
- Define timeout, retry, and idempotency behavior deliberately.

Deep guidance:
- `references/error-strategy.md`
- `references/retryability-classification.md`
- `references/retries-timeouts.md`

## 5) Testing

- Use `pytest` to verify behavior and contracts, not implementation details.
- Keep unit tests fast, deterministic, and isolated from real network/filesystem/wall-clock dependencies.
- Patch and mock at module boundaries and at the import location used by the unit under test.
- Use integration tests for module and dependency contracts, including timeout/retry/cancellation paths where relevant.
- Cover edge cases, failure paths, and regression scenarios for each fixed bug.
- If source-code intent is ambiguous while writing tests, call out assumptions and ask clarifying questions before encoding behavior.
- In test-only tasks, keep source-code improvements as recommendations only; do not implement production changes.
- For dependency updates, run `scripts/test_pypi_security_audit.py`; for async lifecycle changes, run `pyleak` diagnostics.

Deep guidance:
- `references/testing-strategy.md`
- `references/pytest-practices.md`
- `references/async-and-concurrency-testing.md`
- `references/reliability-lifecycle-testing.md`

## 6) Data & State

- Make ownership of data and invariants explicit per module.
- Validate at ingress and normalize before domain decisions.
- Share cross-module data through minimal immutable DTO/value objects.
- Treat each module as a consistency boundary; avoid cross-module transactions.
- Keep configuration typed, environment-driven, and startup-validated.

Deep guidance:
- `references/data-lifecycle.md`
- `references/consistency-boundaries.md`
- `references/configuration.md`

## 7) Concurrency & Performance

- Choose concurrency model by workload, not preference.
- Keep cancellation, deadlines, and cleanup behavior explicit.
- In notebook kernels, treat the event loop as host-owned; use top-level `await` and task orchestration instead of `asyncio.run`.
- Measure before optimizing and re-measure after changes.
- Optimize bottlenecks only after correctness is established.

Deep guidance:
- `references/concurrency-models.md`
- `references/deadlines-cancellation-lifecycle.md`
- `references/leak-detection.md`
- `references/notebooks-async.md`

## 8) External Integrations & Resilience

- Hide external APIs behind explicit client boundaries.
- Require timeout, retry, and idempotency policy for outbound calls.
- Keep domain logic isolated from provider-specific details.
- Test integration contracts and failure behavior directly.

Deep guidance:
- `references/client-patterns.md`
- `references/request-reliability-policy.md`
- `references/resilience-and-contract-testing.md`

## 9) Operations (Services/Jobs/CLI)

- Emit structured logs with stable keys and operation context.
- Track core runtime signals: latency, errors, retries, throughput.
- Validate runtime config at startup.
- Ensure graceful shutdown and cleanup behavior.

Deep guidance:
- `references/runtime-behavior.md`
- `references/logging-metrics-tracing.md`
- `references/process-lifecycle-and-cleanup.md`

## Clarification Rules

Ask concise questions before coding when:

- Repo conventions conflict with this guide.
- Behavior or contracts are ambiguous.
- Reliability policy is unspecified for external operations.
- Boundary modeling is unclear (domain type vs pydantic schema).
- A preferred default appears counterproductive and alternative approaches need tradeoff decisions.
