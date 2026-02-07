---
name: python-workflow-delivery
description: Provides Python workflow and delivery standards. Use when preparing branches, commits, validation gates, and PR readiness for Python changes.
---

# Python Workflow and Delivery

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Invocation Notice

- Inform the user when this skill is being invoked by name: `python-workflow-delivery`.

## Overview

Use this skill for branch-to-PR execution discipline on Python work.
Apply these defaults before opening or updating a PR.

## Core Defaults

- Use the project-defined Python version first.
- Use `uv` for environment and dependency workflow.
- Run checks with `uv run ...`.
- Keep scope small, reversible, and reviewable.

## Validation Gate

Run as required by project scope:

- `uv sync`
- `uv sync --locked`
- `uv lock --check`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run pytest`

Change-specific checks:

- Dependency/lockfile changes: `uv run pytest scripts/test_pypi_security_audit.py -v`
- Async lifecycle changes: run `pyleak` diagnostics on representative async integration tests.

## References

- `references/workflow.md`
- `references/branch-commit-scope.md`
