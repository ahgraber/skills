# Process Lifecycle and Cleanup (Workers/Subprocesses)

## Outcome

Long-running jobs terminate cleanly, classify failures for recovery, and leave no leaked resources.

## Process Group Isolation

- For POSIX subprocess trees, isolate work in its own process group (`os.setpgrp()` / `os.killpg(...)` pattern).
- On shutdown/cancel, send `SIGTERM` first and allow a grace period before `SIGKILL`.
- Catch `ProcessLookupError` (`ESRCH`) during termination and log it as already-exited work.

## Retryability Classification

- Classify exceptions by caller action, not dependency origin.
- Mark transient failures as `retryable=True` and permanent failures as `retryable=False`.
- Include machine-readable metadata on errors (for example `retryable: bool`, error `kind`).
- Use attribute-based fallback (`getattr(error, "retryable", True)`) for compatibility during migration.

## Cleanup Guarantees

- Ensure temporary files, subprocess handles, and open descriptors are cleaned in `try/finally`.
- Log process-group termination and cleanup milestones with job ID and phase.
- Measure cancellation/cleanup latency and enforce upper bounds.

## Verification

- Add integration tests that verify no zombie processes remain after cancellation.
- Assert temporary directories and files are removed on both success and failure.
- Verify critical file/socket handles are closed after terminal states.
- Validate retryable vs permanent terminal states in job result persistence.
