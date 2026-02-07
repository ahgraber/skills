---
name: python-concurrency-performance
description: Provides Python concurrency and lifecycle guidance. Use when choosing concurrency models, handling deadlines/cancellation, or validating leak-free async behavior.
---

# Python Concurrency and Performance

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Invocation Notice

- Inform the user when this skill is being invoked by name: `python-concurrency-performance`.

## Overview

Use this skill for concurrency model selection, cancellation/deadline behavior, and lifecycle safety under load.

## Core Rules

- Choose model by workload, not preference.
- Keep cancellation and cleanup explicit.
- Bound fan-out/backpressure explicitly.
- Measure before optimizing and re-measure after changes.
- Verify no task/thread leaks on lifecycle-sensitive changes.

## References

- `references/concurrency-models.md`
- `references/deadlines-cancellation-lifecycle.md`
- `references/leak-detection.md`
