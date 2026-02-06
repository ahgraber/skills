# Pytest Practices

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Baseline Commands

- Run default suite: `uv run pytest`
- Run a focused file or node: `uv run pytest tests/path/test_module.py::test_case`
- Use markers for scoped runs (if configured): `uv run pytest -m "not slow"`
- Run dependency security audit suite: `uv run pytest scripts/test_pypi_security_audit.py -v`
- Keep CI and local arguments aligned to reduce parity failures.

## Structure and Naming

- Use Arrange-Act-Assert flow.
- Use descriptive names that encode behavior and scenario.
- Prefer plain test functions over class wrappers unless class grouping adds clear value.
- Mirror source modules for unit tests; organize integration tests by scenario/contract.
- Prefer a consistent, behavior-oriented naming convention (for example `test_<unit>_<scenario>_<expected_result>`).

## Tests as Documentation

- Treat tests as user-facing documentation for how code should and should not be used.
- Keep naming explicit and behavior-oriented; avoid vague names like `test_1` or `test_misc`.
- Add concise docstrings to tests when intent is not obvious from the name alone.
- Write assertion error messages when they materially improve diagnosis (especially for parameterized or contract-heavy tests).
- Add brief comments only for non-obvious setup, invariants, or domain context; avoid narrating trivial steps.

## Fixtures

- Use fixtures for reusable setup and teardown.
- Keep fixture scope as narrow as practical (`function` by default).
- Prefer explicit fixture dependencies over hidden autouse fixtures.
- Keep fixtures small and behavior-focused; avoid large fixture graphs that hide intent.

## Mocking and Patching

- Mock only external boundaries (I/O, network, time, randomness, external services).
- Patch where the symbol is looked up by the unit under test (import location), not where it was originally defined.
- Prefer `monkeypatch` for simple env/attribute patching and `unittest.mock` for call assertions or complex behavior.
- Use `spec`/`autospec` when practical to catch invalid attribute or call usage.
- Do not assert mock internals when a direct behavior assertion is available.

## Parametrization

- Use `pytest.mark.parametrize` for input matrices.
- Add readable `id` values for complex cases.
- Keep parameter sets behavior-focused (inputs and expected contract outcomes).

## Async and Reliability

- Use `pytest-asyncio` for asyncio-based tests when the project uses asyncio.
- Set `asyncio_mode` explicitly in project config (`strict` or `auto`) and follow project convention.
- Test timeout and cancellation behavior explicitly for async operations.
- For long-running async work, assert cleanup and terminal state behavior (not just raised exception type).
- Run leak diagnostics with `pyleak` for async-heavy changes and cancellation/deadline refactors.

## Determinism

- Freeze or inject time and randomness.
- Avoid real sleeps in unit tests; use bounded synchronization primitives or controlled clocks.
- Ensure tests pass in random order and on repeated runs.

## Test-Only Scope Rule

- When the task is test-only, do not modify production/source code.
- If code changes would improve clarity or testability, document them as recommendations and keep implementation out of the test change.
