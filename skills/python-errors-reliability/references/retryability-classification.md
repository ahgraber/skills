# Retryability Classification

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## When to Apply

- Apply this guidance when the system performs automatic retries (workers, jobs, outbound integration calls, orchestration loops).
- Skip this layer for local-only logic where failures are returned directly to a caller and no retry mechanism exists.

## Outcome

Failure handling produces consistent retry decisions and terminal states.

## Classification Rules

- Encode retryability as explicit policy data (for example, error metadata or a centralized exception/status mapping), not string matching.
- Classify transient dependency failures as retryable (network timeouts, temporary 5xx, 429, interrupted workers).
- Classify caller/data/contract failures as permanent (validation, authz/authn, schema mismatch, integrity violations).
- Choose and document a safe default when retryability is unknown; the default should match system risk and idempotency guarantees.

## Terminal State Rules

- Persist terminal outcome with a clear retryable vs permanent distinction using project-defined status names.
- Store enough context for diagnosis and replay decisions (error kind, phase, attempt count, elapsed/deadline).
- Ensure cleanup runs before terminal state is recorded when work is cancellable or multi-phase.

## Validation Checklist

- Unit-test classification mapping for each known error kind.
- Integration-test timeout, cancellation, and retry-budget exhaustion paths.
- Verify no duplicate logs per failure and no silent drops of permanent failures.
