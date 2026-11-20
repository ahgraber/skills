# Python Testing Practices

This reference extends the language-agnostic foundations in the `writing-tests` skill (AAA structure, naming, test-doubles taxonomy, portfolio strategy, write-site and derived-pair coverage patterns) with Python-specific practice.
The same file ships in both the `python` and `writing-tests` skills.

## `unittest.mock` discipline

**The naming is misleading.** `Mock` and `MagicMock` behave as Stubs by default — configured via `return_value` or `side_effect`, they return canned values and do not self-verify.
They become Mocks (behavior verification) only when you call `.assert_called_with()` / `.assert_called_once_with()`.
Prefer asserting on observable output instead.

**Use `create_autospec()` or `autospec=True`.**
A plain `Mock()` accepts any arguments silently.
`create_autospec(SomeClass)` enforces the real method signatures: a call-site mismatch fails the test immediately rather than hiding a `TypeError` until production.

**Patch at the import location used by the module under test**, not at the original definition site:

```python
# Wrong: patches the definition; callers in other modules are unaffected
patch("requests.post", ...)

# Right: patches where your module imported it
patch("mymodule.client.requests.post", ...)
```

**Choose the lightest tool.**
Prefer `monkeypatch` for simple env/attribute patching and `unittest.mock` for call assertions or complex behavior.
Use `pytest-mock`'s `mocker` fixture when the project already depends on it (it handles teardown via the fixture lifecycle), but do not add the dependency solely for ergonomics.

**Prefer fakes to deep mock chains.**
An in-memory implementation (`FakeRepo`, a `dict`-backed store) replaces a multi-level `Mock()` chain.
Chains that mirror the production call graph are brittle and a sign that I/O has not been decoupled from logic.

## Pytest structure

- Prefer plain test functions over class wrappers unless grouping adds clear value.
- Mirror source modules for unit tests; organize integration tests by scenario or contract.
- Keep fixture scope as narrow as practical (`function` by default); prefer explicit fixture dependencies over hidden `autouse` fixtures.
- Use `pytest.mark.parametrize` for input matrices, with readable `id` values for complex cases.

## Test docstrings

Document the contract under test, not the mechanics.
Use the shortest form that captures contract, error path, and the implication of a regression:

- `Validates: <rule or invariant>`
- `Error path: <trigger> -> <expected handling/outcome>`
- `Implication: <what breaks or becomes risky if this regresses>`

```python
def test_retry_budget_exhaustion_marks_job_failed(job_runner):
    """Validates: retries stop at configured budget and state becomes terminal.
    Error path: transient dependency failures exceed retry budget -> permanent failed state.
    Implication: prevents silent infinite retries and queue starvation under outages."""
```

## Async testing

- Use `pytest-asyncio` when the project uses asyncio; set `asyncio_mode` explicitly in project config (`strict` or `auto`) and follow project convention.
- Test timeout and cancellation paths explicitly; for long-running async work, assert cleanup and terminal state, not just the raised exception type.
- Avoid sleep-based assertions for scheduling-sensitive behavior; use explicit coordination points.
- Run `pyleak` diagnostics on representative async integration tests when a change affects task lifecycle, deadlines, cancellation, or worker orchestration.
  Treat `pyleak` as dev/test tooling, not a runtime dependency.
- Assert that no tasks or threads remain leaked at test completion.

## Dependency audits

For dependency or lockfile changes, run the supply-chain audit scripts shipped in the `python` skill's `scripts/`.
Run from the target project's root, passing each script by its full path:

```sh
uv run pytest <path-to-python-skill>/scripts/test_uv_security_audit.py <path-to-python-skill>/scripts/test_pypi_security_audit.py -v
```

`test_uv_security_audit.py` uses `uv audit` against the lockfile and is preferred; `test_pypi_security_audit.py` is the pip-audit fallback and auto-skips when uv audit can run.
Both scripts probe `uv audit --help` rather than parsing a version, so a uv build too old for the audit command (or for its JSON output) falls through to pip-audit instead of failing.
Both warn (not fail) on findings, so read the warnings.

## Multi-version testing

For test matrices across Python versions (nox + uv configuration, CI patterns, dependency-matrix parametrization), see `references/multi-python-testing.md` in the `python` skill.
