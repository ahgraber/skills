---
name: python-errors-reliability
description: Provides Python error and reliability policy. Use when implementing timeout, retry, idempotency, retryability, or failure-translation behavior.
---

# Python Errors and Reliability

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Invocation Notice

- Inform the user when this skill is being invoked by name: `python-errors-reliability`.

## Overview

Use this skill when failure handling semantics materially affect behavior and operations.
Design errors so callers can act and operators can diagnose quickly.

## Core Rules

- Preserve cause chains at translation boundaries.
- Catch only what can be handled.
- Keep timeout/deadline policy explicit.
- Keep retry policy explicit and bounded.
- Classify retryable vs permanent failures with explicit policy data.
- Keep idempotency expectations explicit for retried writes.

## References

- `references/error-strategy.md`
- `references/retryability-classification.md`
- `references/retries-timeouts.md`
