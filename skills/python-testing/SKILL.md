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

For language-agnostic testing principles (AAA structure, naming, test doubles taxonomy, portfolio strategy), see `writing-tests`.
This skill extends those foundations with Python-specific practices.

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
- Add regression tests for bugfixes — write the failing test before the fix.
- Include timeout/retry/cancellation/cleanup coverage where relevant.
- For multi-Python: use nox with uv backend; parametrize for dependency matrices.
- For free-threaded Python: use `pytest-run-parallel`, set `PYTHON_GIL=0`, always set CI timeouts.

## Test Doubles

See `writing-tests` → `references/test-doubles.md` for the full Meszaros taxonomy (Dummy, Fake, Stub, Spy, Mock), the classical vs. mockist distinction, and general guidance.
Python-specific notes:

**`unittest.mock` naming is misleading.**
`Mock` and `MagicMock` are named "Mock" but behave as Stubs by default — configured via `return_value` or `side_effect`, they return canned values and do not self-verify.
They become Mocks (behavior verification) only when you call `.assert_called_with()` / `.assert_called_once_with()`.
Prefer asserting on observable output instead.

**Use `create_autospec()` or `autospec=True`.**
A plain `Mock()` accepts any arguments silently.
`create_autospec(SomeClass)` enforces the real method signatures — a call-site mismatch fails the test immediately rather than hiding a `TypeError` until production.

**Patch at the import location used by the module under test**, not at the original definition site:

```python
# Wrong: patches the definition; callers in other modules are unaffected
patch("requests.post", ...)

# Right: patches where your module imported it
patch("mymodule.client.requests.post", ...)
```

**Consider `pytest-mock`'s `mocker` fixture** if the project already uses it.
It integrates with pytest's fixture lifecycle, handles teardown automatically, and avoids decorator stacking on test functions.
`unittest.mock.patch` is sufficient when `pytest-mock` is not already a dependency — adding it solely for ergonomics is not warranted.

**Fakes over deep mock chains.**
Prefer in-memory implementations (`FakeRepo`, a `dict`-backed store) over multi-level `Mock()` chains.
Chains that mirror the production call graph are brittle and a sign that I/O has not been decoupled from logic.

## Change-Specific Diagnostics

- Dependency updates: run `uv run pytest scripts/test_uv_security_audit.py scripts/test_pypi_security_audit.py -v`.
  `test_uv_security_audit.py` uses `uv audit` against the lockfile and is preferred; `test_pypi_security_audit.py` is the pip-audit fallback that auto-skips when uv audit can run.
  Both warn (not fail) on findings, so review the warnings.
- Async-heavy lifecycle changes: run `pyleak` diagnostics.
- Multi-Python support changes: run full matrix via `nox`.
- Free-threaded compatibility: run `PYTHON_GIL=0 uv run --python 3.Xt pytest --parallel-threads=auto --timeout=300` on a free-threaded build (3.13t+).

## Common Mistakes

- **Single write-site coverage** — testing the canonical code path but not alternative paths (dedup shortcut, cache fast-path, retry branch) that write the same contract-asserted value.
  Each write-site needs its own test.
  See `references/testing-strategy.md` § Multi-Path and Derived-Field Patterns.
- **Missing post-composition invariant** — when `field_a == f(field_b)` is a required relationship and each field is written by a different producer (resolver, fetcher, merge step), stage-local tests don't prove the invariant holds after composition.
  Write a test that asserts the relationship on the assembled output.
  See `references/testing-strategy.md` § Multi-Path and Derived-Field Patterns.
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
- `writing-tests` skill — language-agnostic foundations (AAA, naming, test doubles, portfolio strategy)
