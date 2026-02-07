---
name: python-runtime-operations
description: Provides Python runtime operations guidance. Use when implementing service, job, or CLI behavior for startup, shutdown, observability, and cleanup.
---

# Python Runtime Operations

## Overview

Use this skill for operational runtime behavior in services, workers/jobs, and CLI entrypoints.

## Core Rules

- Validate runtime config at startup.
- Ensure graceful shutdown and bounded cleanup.
- Make retry/dead-letter terminal-state behavior explicit for job systems.
- Emit structured logs and track core runtime signals.

## References

- `references/runtime-behavior.md`
- `references/logging-metrics-tracing.md`
- `references/process-lifecycle-and-cleanup.md`
