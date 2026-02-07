# Deadlines, Cancellation, and Process Lifecycle

## Outcome

Concurrent operations stop predictably, clean up completely, and report actionable failure states.

## Deadline Policy

- Use absolute deadlines based on monotonic time (`time.monotonic() + timeout`).
- Pass deadlines through nested calls instead of recomputing ad hoc relative timeouts.
- Check deadline at critical checkpoints (poll loops, retries, phase transitions).
- Include elapsed time and phase in timeout errors/logs.

## Cancellation Policy

- Treat cancellation as a normal control-flow outcome, not an unexpected error.
- Handle `asyncio.CancelledError` only to run local cleanup, then re-raise.
- Do not swallow cancellation in leaf tasks; it breaks structured concurrency semantics.

## Process and Subprocess Lifecycle

- Isolate child work in its own process group/session (`os.setpgrp()` or `start_new_session=True`).
- Terminate process groups explicitly (`os.killpg(pgid, signal.SIGTERM)`), then escalate to `SIGKILL` after a grace window.
- Catch and log `ProcessLookupError` (`ESRCH`) during teardown when children already exited.
- Make shutdown idempotent: repeated cleanup calls must be safe.

## Retryability and Terminal State

- Classify failure as retryable vs permanent using explicit policy data (for example, `error.retryable` or centralized mapping rules).
- Define and document a safe default for unknown retryability that matches idempotency and system risk.
- Mark deadline exceeded, transient I/O, and interruption cases as retryable by default.
- Mark invalid input/data integrity/contract violations as permanent failures.
- Persist terminal state with enough context for replay and diagnosis.

## Validation

- Integration tests should assert no zombie children, leaked temp directories, or open-handle leaks.
- Test timeout and cancellation paths explicitly, including mid-phase cancellation.
