---
name: python-concurrency-performance
description: Provides Python concurrency and lifecycle guidance. Use when choosing concurrency models, handling deadlines/cancellation, or validating leak-free async behavior.
---

# Python Concurrency and Performance

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
