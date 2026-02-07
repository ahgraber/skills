# Runtime Behavior (Services, Jobs, CLI)

## Outcome

Runtime behavior is predictable under startup, load, retries, cancellations, and shutdown.

## Startup

- Validate required config at startup with typed settings.
- Fail fast on invalid critical settings.
- Log service version/build metadata once at startup.

## Shutdown and Cancellation

- Handle termination signals explicitly.
- Stop intake before teardown and drain in-flight work within a bounded deadline.
- Cleanup subprocesses, temporary files, and open handles in `try/finally` or context managers.

## Deadlines and Timeouts

- Prefer absolute deadlines (`time.monotonic() + budget`) for long-running operations.
- Check deadlines at critical checkpoints (poll loops, retries, phase transitions).
- Include phase and elapsed time in timeout exceptions and logs.

## Jobs and Workers

- Model state transitions explicitly (`pending`, `running`, `succeeded`, `failed`, `cancelled`, `dead_letter` as needed).
- Record retryable and permanent terminal states distinctly.
- Persist attempt count, last error kind, and phase for replay/diagnosis.
- Keep backoff, retry caps, and dead-letter policy explicit.

## CLI Behavior

- Return meaningful, stable exit codes.
- Emit concise human-readable output and structured logs where appropriate.
- Write errors to stderr and avoid hiding failures behind broad exception handling.
