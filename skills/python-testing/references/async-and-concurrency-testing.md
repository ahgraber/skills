# Async and Concurrency Testing

## Outcome

Async and concurrent behavior is validated for correctness, cancellation safety, and cleanup.

## When to Apply

- Asyncio call paths (`async def`, task orchestration, timeouts, cancellation).
- Worker or background task coordination.
- Changes affecting deadlines, retry loops, or bounded concurrency.

## Test Focus Areas

- Successful async behavior and expected results.
- Timeout paths (deadline exceeded, retry budget exhausted).
- Cancellation behavior (`CancelledError` propagation after local cleanup).
- Bounded fan-out/backpressure behavior when queues/semaphores are used.
- Task and resource cleanup after success, failure, and cancellation.

## Practical Rules

- Keep async unit tests deterministic and fast.
- Use `pytest-asyncio` configuration defined by the project; set `asyncio_mode` explicitly.
- Avoid custom event-loop fixture overrides unless required by project constraints.
- Avoid sleep-based assertions for scheduling-sensitive behavior; use explicit coordination points.
- For notebooks or loop-owned environments, keep async orchestration at the boundary and test reusable logic in normal modules.

## Leak Diagnostics

- Use `pyleak` (sometimes referred to as "pyleaks") as a dev/test diagnostic for leaked asyncio tasks, leaked threads, and event-loop blocking.
- Run leak checks on representative async integration tests when changes affect task lifecycle, deadlines, cancellation, or worker orchestration.
- Treat `pyleak` as test/developer tooling, not a required runtime dependency.

## Validation Signals

- No leaked tasks/threads at test completion.
- Deadlines are enforced at known checkpoints.
- Cancellation leaves system state consistent and replay-safe.
