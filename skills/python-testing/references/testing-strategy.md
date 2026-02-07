# Testing Strategy

## Outcome

Tests that prove behavior and contracts, prevent regressions, and support safe refactoring.

## Reference Map

- `pytest-practices.md`
- `async-and-concurrency-testing.md`
- `reliability-lifecycle-testing.md`

## Contract-First Rules

- Assert observable behavior (outputs, state transitions, emitted effects), not private implementation details.
- Do not lock tests to internals (private helpers, incidental call order, exact log strings) unless those details are part of the explicit public contract.
- Add a regression test for every fixed bug.
- Keep one primary behavior per test unless assertions are tightly coupled.

## Determine Intent and Contracts

- Infer intended behavior from names, docstrings, type hints, usage patterns, and existing tests before adding or revising tests.
- If intent is ambiguous or underspecified, state assumptions explicitly and ask clarifying questions before encoding behavior in tests.
- Treat tests as executable contract documentation for expected and disallowed usage.

## Test Portfolio

- Unit tests:
  - Fast, deterministic, and isolated.
  - No real network, filesystem, database, or sleep-based timing.
  - Mock/fake only at module boundaries.
- Integration tests:
  - Verify module and dependency contracts, including schema and error translation boundaries.
  - Exercise reliability policy where relevant (timeouts, retries, cancellation, idempotency assumptions).
- End-to-end tests:
  - Keep a minimal set of high-value, business-critical user flows.
  - Prefer stability and signal quality over broad scenario volume.

## Coverage Expectations

- Happy path and primary alternatives.
- Validation failures and error paths.
- Edge conditions and boundary inputs.
- Regression tests for every fixed bug.
- For reliability-sensitive code, include timeout/cancellation and cleanup behavior.
- For dependency/lockfile changes, include the PyPI vulnerability audit suite (`scripts/test_pypi_security_audit.py`).

## Determinism and Flake Control

- Keep tests order-independent and free of shared mutable global state.
- Control time, randomness, and environment through fixtures or injected dependencies.
- Prefer explicit synchronization over sleep-based timing.
- Use realistic fixtures where contract shape matters.

## Review Checklist

- The tests would fail for a behavior regression, not just an implementation rewrite.
- Unit and integration boundaries are clear and intentional.
- Reliability paths are covered when the change touches external I/O or long-running work.
- Async-heavy changes include leak diagnostics using `pyleak`.
- New tests are maintainable and understandable without reading private implementation code.
- If source code clarity/testability issues are found while writing tests, they are listed as recommendations only and not implemented in the same test-only change.
