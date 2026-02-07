# Leak and Blocking Diagnostics

## Outcome

Concurrency regressions (task leaks, thread leaks, event-loop blocking) are detected early with actionable stack traces.

## Tooling Guidance

- Use [`pyleak`](https://github.com/deepankarm/pyleak) as a developer diagnostic for leaked `asyncio` tasks, leaked threads, and event-loop blocking.
- Treat `pyleak` as dev/test tooling, not a required runtime dependency.
- Run leak checks for async-heavy changes, worker lifecycle changes, and cancellation/deadline refactors.

## Usage Policy

- Run diagnostics on representative integration tests or realistic local workloads.
- Capture findings (including stack traces) in PR notes when concurrency behavior changes materially.
- Fix leak/blocking findings before merge, or document an explicit temporary exception with owner and follow-up date.
