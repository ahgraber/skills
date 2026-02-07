# Outbound Request Reliability Policy

## Outcome

Outbound calls fail predictably without retry storms, duplicated writes, or hidden latency.

## Timeout and Deadline Rules

- Set explicit timeouts for all outbound I/O.
- Prefer end-to-end deadlines over uncoordinated per-layer relative timeouts.
- Pass deadline/budget through nested calls and retry loops.
- Include elapsed time and phase when raising timeout failures.

## Retry Rules

- Retry only transient failures (timeouts, temporary transport failures, retryable 5xx, throttling).
- Treat validation, auth, and contract/schema violations as permanent.
- Keep retries in one layer only (client or caller), never both.
- Bound retries by attempt count and remaining deadline.
- Use exponential backoff with jitter for retry spacing.
- Respect server-provided retry delay hints (for example, `Retry-After`) when present.

## Idempotency and Write Safety

- Align retry behavior with HTTP semantics: treat `GET`/`HEAD` as safe reads, `PUT`/`DELETE` as idempotent by contract, and `POST` as non-idempotent unless the API defines idempotency guarantees.
- Retry writes only when idempotency is guaranteed.
- Use idempotency keys or equivalent dedupe tokens for non-idempotent methods (`POST`/`PATCH`) when retries are enabled.
- Propagate operation/request IDs across retries for tracing and deduplication.
- If idempotency cannot be guaranteed, disable automatic retries and surface a clear failure mode.
