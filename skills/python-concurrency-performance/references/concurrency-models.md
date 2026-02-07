# Concurrency Models

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

Correct and maintainable concurrent behavior with explicit operational limits.

## Reference Map

- `deadlines-cancellation-lifecycle.md`
- `leak-detection.md`
- Notebook/ipykernel loop ownership and cell-orchestration patterns: use `python-notebooks-async`.

## Model Selection

- Use `asyncio` for I/O-bound concurrency when dependencies are async-native.
- Use threads for blocking I/O or sync-library adapters (`asyncio.to_thread()` from async code).
- Use processes for CPU-bound work or hard isolation requirements.
- Set process start method explicitly for cross-platform behavior when process pools are critical.

## Structured Concurrency Defaults

- Prefer `asyncio.TaskGroup` for scoped fan-out/fan-in work.
- Keep task lifetime bounded to the owning operation; avoid fire-and-forget tasks in request paths.
- Use `asyncio.gather()` deliberately when partial-success semantics are required.

## Backpressure and Work Bounding

- Bound fan-out with explicit limits (`Semaphore`, bounded queues, worker caps).
- Keep queue sizes finite to avoid unbounded memory growth under load.
- Make overload behavior explicit: block, shed, or degrade.

## Boundary Rules

- Keep a call path fully sync or async; use explicit adapters at boundaries.
- Never block the event loop with sync network, file I/O, or CPU-heavy loops.
- In reusable libraries, avoid loop ownership (`asyncio.run`) and expose awaitable APIs to callers.
- Define ownership for cancellation and cleanup at each boundary.

## Reliability

- Propagate deadlines into nested operations.
- Handle cancellation as a first-class outcome.
- Ensure cleanup in `finally` or managed contexts.
