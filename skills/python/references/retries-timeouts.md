# Retries, Timeouts, and Edge Cases

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

External operations fail predictably without retry storms or hidden latency.

## Timeout and Deadline Policy

- Set explicit timeouts for all external I/O.
- Prefer absolute deadlines (`time.monotonic() + budget`) over ad hoc relative timeouts.
- Pass deadline/budget through nested calls instead of recomputing per layer.
- Check deadline at critical checkpoints (poll loops, retries, phase transitions).
- Include elapsed time and phase in timeout errors and logs.

## Retry Policy

- Retry only transient failures (timeouts, temporary unavailability, rate limiting).
- Do not retry permanent failures (invalid input, auth failures, contract violations, data integrity errors).
- Keep retries in one layer to avoid multiplicative retry storms.
- Bound retries by both attempt count and total deadline.
- Use exponential backoff with jitter and a max sleep cap.
- Log retry attempts with attempt number, delay, and reason.

## Idempotency and Writes

- Require idempotency keys or equivalent dedupe strategy before retrying write operations.
- If writes are not idempotent, do not auto-retry unless compensating behavior is defined.
- Propagate request/operation IDs so retries can be traced and deduplicated.

## Edge Case Guidance

- Define behavior for partial failures explicitly (per-item status, not opaque batch failure).
- Distinguish retryable terminal states from permanent terminal states.
- Test boundary values, empty/minimal inputs, and exhausted retry budgets.
