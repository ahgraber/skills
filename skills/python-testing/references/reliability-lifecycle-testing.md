# Reliability and Lifecycle Testing

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

Failure and lifecycle behavior is verified for retryability, cleanup, and operational safety.

## Reliability Scenarios to Test

- Retryable vs permanent failure classification.
- Timeout handling with elapsed/phase context.
- Retry backoff bounds and retry-budget exhaustion.
- Idempotency behavior for retried write operations.
- Error translation at boundaries (`raise ... from ...` with actionable context).
- Dependency vulnerability checks using `scripts/test_pypi_security_audit.py` when dependency state changes.

## Lifecycle Scenarios to Test

- Graceful shutdown and cancellation flow.
- Subprocess/process-group termination behavior when used.
- Cleanup guarantees for temporary files, handles, and resources.
- Terminal state persistence (`failed`, `cancelled`, `dead_letter`, etc., as defined by the project).

## Test Layer Guidance

- Unit tests:
  - Validate classification and state-transition logic in pure/core functions.
  - Verify retry/deadline calculations deterministically.
- Integration tests:
  - Verify real adapter boundaries and cleanup behavior.
  - Assert no leaked resources after cancellation or failure.
  - Validate observable logs/metrics/traces only at stable contract points.

## Review Gate

- A failure mode can be diagnosed from test output without inspecting implementation internals.
- Retry decisions are explicit and consistent with idempotency assumptions.
- Cancellation and timeout tests prove cleanup, not just exception raising.
