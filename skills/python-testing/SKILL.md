---
name: python-testing
description: |-
  Use when writing or reviewing tests for Python behavior, contracts, async lifecycles, or reliability paths. Also use when tests are flaky, coupled to implementation details, missing regression coverage, slow to run, or when unclear what tests a change needs. Use for multi-Python version testing (nox) and free-threaded Python thread-safety validation.
---

# Python Testing

## Overview

Test observable behavior and contracts, not internal implementation.
Keep unit tests fast, deterministic, and patched at module boundaries.

These are preferred defaults for common cases.
When a default conflicts with project constraints, suggest a better-fit alternative, call out tradeoffs, and note compensating controls.

## Invocation Notice

- Inform the user when this skill is being invoked by name: `python-testing`.

## When to Use

- Writing or reviewing unit, integration, or reliability-sensitive tests.
- Tests are flaky, slow, or coupled to implementation details.
- Adding regression tests after a bugfix.
- Testing async lifecycles, cancellation, or cleanup paths.
- Unsure what test coverage a change needs.
- Testing across multiple Python versions (nox, CI matrix).
- Validating thread safety for free-threaded Python (GIL-disabled builds).

**When NOT to use:**

- Pure data-shape or schema validation (see `python-types-contracts`).
- Production observability or monitoring concerns (see `python-runtime-operations`).
- Concurrency design decisions outside of test harnesses (see `python-concurrency-performance`).

## Quick Reference

- Test observable behavior, not internals.
- Keep unit tests fast and deterministic.
- Patch at module boundaries and import locations used by the unit under test.
- Add regression tests for bugfixes.
- Include timeout/retry/cancellation/cleanup coverage where relevant.
- For multi-Python: use nox with uv backend; parametrize for dependency matrices.
- For free-threaded Python: use `pytest-run-parallel`, set `PYTHON_GIL=0`, always set CI timeouts.

## Change-Specific Diagnostics

- Dependency updates: run `uv run pytest scripts/test_pypi_security_audit.py -v`
- Async-heavy lifecycle changes: run `pyleak` diagnostics.
- Multi-Python support changes: run full matrix via `nox`.
- Free-threaded compatibility: run `PYTHON_GIL=0 uv run --python 3.Xt pytest --parallel-threads=auto --timeout=300` on a free-threaded build (3.13t+).

## Common Mistakes

- **Mocking too deep** — patching internals instead of module-boundary seams makes tests brittle and coupled to implementation.
- **Testing the mock** — verifying mock call counts without asserting on observable output proves nothing about behavior.
- **Missing regression test** — fixing a bug without a test that reproduces it first; the bug will recur.
- **Non-deterministic time/order** — relying on wall-clock time or dict/set ordering instead of injecting clocks and sorting explicitly.
- **Skipping cleanup assertions** — verifying the happy path but never asserting that resources are released on failure or cancellation.
- **No free-threaded CI entry** — shipping multi-threaded code without a free-threaded (`t`-suffixed) matrix entry; the GIL hides race conditions that will surface when free-threaded Python becomes the default.
- **Ignoring GIL re-enablement** — importing a C extension without `Py_mod_gil` silently re-enables the GIL; check `sys._is_gil_enabled()` after imports.
- **YAML version float** — writing `3.10` unquoted in CI matrix YAML; it parses as `3.1` and installs the wrong Python.

## References

- `references/testing-strategy.md`
- `references/pytest-practices.md`
- `references/async-and-concurrency-testing.md`
- `references/reliability-lifecycle-testing.md`
- `references/multi-python-testing.md`
- `references/free-threaded-testing.md`
