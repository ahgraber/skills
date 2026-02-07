# Resilience and Contract Testing

## Outcome

Integration behavior is verified at provider boundaries before production incidents force discovery.

## Failure-Path Tests

- Timeout paths.
- Retry decisions, backoff bounds, and retry-budget exhaustion.
- Partial failures and fallback behavior.
- Non-retryable vs retryable classification.
- Cancellation cleanup paths (propagate cancellation after local cleanup).

## Contract Test Rules

- Assert required request fields, headers, and idempotency metadata.
- Assert response schema validation and mapping into local DTOs/errors.
- Assert provider error/status mapping into local retryability policy.
- Keep fixtures realistic enough to detect contract drift.

## Operational Guardrails

- Emit structured logs at failure boundaries with operation ID, provider, attempt, and phase.
- Track dependency latency, error rate, retries, and permanent-failure rate separately.
- Alert on sustained retry growth, timeout growth, and elevated 429/5xx responses.
- Use events/jobs for cross-module workflows instead of synchronous domain call chains.
