---
name: python-testing
description: Provides Python testing strategy and pytest practices. Use when creating or reviewing tests for behavior, contracts, async/concurrency, and reliability paths.
---

# Python Testing

## Overview

Use this skill to design tests that prove behavior and contracts while staying deterministic and maintainable.
Apply it for unit, integration, and reliability-sensitive changes.

## Core Rules

- Test observable behavior, not internals.
- Keep unit tests fast and deterministic.
- Patch at module boundaries and import locations used by the unit under test.
- Add regression tests for bugfixes.
- Include timeout/retry/cancellation/cleanup coverage where relevant.

## Change-Specific Diagnostics

- Dependency updates: run `uv run pytest scripts/test_pypi_security_audit.py -v`
- Async-heavy lifecycle changes: run `pyleak` diagnostics.

## References

- `references/testing-strategy.md`
- `references/pytest-practices.md`
- `references/async-and-concurrency-testing.md`
- `references/reliability-lifecycle-testing.md`
