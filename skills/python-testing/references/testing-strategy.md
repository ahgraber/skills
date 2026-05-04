# Testing Strategy

## Outcome

Tests that prove behavior and contracts, prevent regressions, and support safe refactoring.

## Reference Map

- `pytest-practices.md`
- `async-and-concurrency-testing.md`
- `reliability-lifecycle-testing.md`

## Contract-First Rules

- Assert observable behavior (outputs, state transitions, emitted effects), not private implementation details.
- Do not lock tests to internals (private helpers, incidental call order, exact log strings) unless those details are part of the explicit public contract.
- Add a regression test for every fixed bug.
  Write the failing test that reproduces the bug _before_ attempting the fix; a green test on a fix you never saw fail does not prove the bug is gone.
- Keep one primary behavior per test unless assertions are tightly coupled.

## Determine Intent and Contracts

- Infer intended behavior from names, docstrings, type hints, usage patterns, and existing tests before adding or revising tests.
- If intent is ambiguous or underspecified, state assumptions explicitly and ask clarifying questions before encoding behavior in tests.
- Treat tests as executable contract documentation for expected and disallowed usage.

## Test Portfolio

Shape the suite as a pyramid: many fast unit tests, fewer integration tests, a small set of end-to-end tests.
As a rough default, target roughly 70-80% unit, 15-25% integration, and under 10% end-to-end.
Treat the ratios as a sanity check against an inverted pyramid (slow, flaky, expensive), not a quota — let contract risk and reliability needs drive the actual mix.

- Unit tests:
  - Fast, deterministic, and isolated.
  - No real network, filesystem, database, or sleep-based timing.
  - Mock/fake only at module boundaries.
- Integration tests:
  - Verify module and dependency contracts, including schema and error translation boundaries.
  - Exercise reliability policy where relevant (timeouts, retries, cancellation, idempotency assumptions).
- End-to-end tests:
  - Keep a minimal set of high-value, business-critical user flows.
  - Prefer stability and signal quality over broad scenario volume.

## Coverage Expectations

- Happy path and primary alternatives.
- Validation failures and error paths.
- Edge conditions and boundary inputs.
- Regression tests for every fixed bug.
- For reliability-sensitive code, include timeout/cancellation and cleanup behavior.
- For dependency/lockfile changes, include the PyPI vulnerability audit suite (`scripts/test_pypi_security_audit.py`).

## Multi-Path and Derived-Field Patterns

These two patterns catch a class of bug where a single happy-path test produces a false sense of coverage.

### Multiple write-sites for the same contract

When a contract-asserted value (a persisted field, a response, an emitted event) can be produced by more than one code path — canonical path plus a deduplication shortcut, retry branch, cache fast-path, idempotency early-return — **each path needs its own test**.

A test that exercises the canonical path does not prove the shortcut is correct, even if the shortcut calls the same underlying function.
The shortcut may skip validation, use a different write order, or fail to propagate updated fields.

Pattern: enumerate write-sites in the implementation; write one test per site that asserts the contract outcome at that site.

```python
def test_persist_provenance_on_fresh_upload(repo, source):
    """Validates: source provenance is persisted on initial upload.
    Implication: fresh-upload path sets canonical fields; regression would silently drop provenance."""
    result = repo.save(source, dedup=False)
    assert result.normalized_url == normalize_url(source.url)


def test_persist_provenance_via_dedup_shortcut(repo, existing_source):
    """Validates: source provenance is preserved when dedup shortcut returns an existing record.
    Implication: dedup path skipping the write would silently lose provenance updates."""
    updated = replace(existing_source, url="https://example.com/new-path")
    result = repo.save(updated, dedup=True)
    assert result.normalized_url == normalize_url(updated.url)
```

### Derived-pair invariants across composition boundaries

When a spec asserts `field_a == f(field_b)` as an invariant — especially when `field_a` and `field_b` are written by different producers (resolver, fetcher, merge step) — **neither stage-local tests nor field-local tests prove the invariant holds after composition**.

Each producer can be correct in isolation while the composition breaks the relationship.
A post-composition invariant test asserts the relationship on the assembled output after all producers have run.

```python
def test_normalized_url_invariant_after_manifest_merge(resolver_output, fetcher_output):
    """Validates: normalized_url == normalize_url(source_url) after resolver+fetcher merge.
    Implication: if merge treats the pair as independent fields, a resolver update would produce
    inconsistent normalized_url without triggering a visible failure."""
    manifest = merge_manifest(resolver_output, fetcher_output)
    assert manifest.normalized_url == normalize_url(manifest.source_url), (
        f"Derived-pair invariant broken: normalized_url={manifest.normalized_url!r} "
        f"!= normalize_url(source_url={manifest.source_url!r})"
    )
```

Identify candidates for this pattern: look for pairs of fields where one is described as derived from the other (in specs, docstrings, or naming), and the fields are written by code that does not enforce the relationship at each write.

## Determinism and Flake Control

- Keep tests order-independent and free of shared mutable global state.
- Control time, randomness, and environment through fixtures or injected dependencies.
- Prefer explicit synchronization over sleep-based timing.
- Use realistic fixtures where contract shape matters.

## Review Checklist

- The tests would fail for a behavior regression, not just an implementation rewrite.
- Unit and integration boundaries are clear and intentional.
- Reliability paths are covered when the change touches external I/O or long-running work.
- Async-heavy changes include leak diagnostics using `pyleak`.
- New tests are maintainable and understandable without reading private implementation code.
- If source code clarity/testability issues are found while writing tests, they are listed as recommendations only and not implemented in the same test-only change.
