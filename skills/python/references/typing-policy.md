# Types and Public Interfaces

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

Predictable interfaces with clear contracts and safer refactoring.

## Public API Typing Baseline

- Type all public functions, methods, and return values.
- Keep annotations current when behavior changes.
- Treat untyped public callables as contract gaps; close them before merge.
- Use type hints to support readability and static analysis, not as optional decoration.

## Modern Annotation Style

- Prefer modern syntax when the supported Python version allows it (typically 3.10+):
  - `list[str]`, `dict[str, int]`, `X | None`
  - avoid legacy `typing.List`/`typing.Dict` in new code unless needed for compatibility with older targets
- For function parameters, prefer abstract interfaces (`Mapping`, `Sequence`, `Iterable`) when callers do not require mutability.
- For return values, use concrete types only when behavior depends on concrete semantics (ordering, mutability, random access).
- Use `Protocol` for boundary-facing behavior contracts to keep coupling low.
- Use `@runtime_checkable` only when runtime `isinstance` checks are truly needed; keep runtime checks out of hot paths.

## Boundary Contract Rules

- Define input and output shapes explicitly.
- Cross-module interaction must occur only through explicit public interfaces.
- Do not leak persistence or framework internals through public APIs.
- Keep module core contracts on plain domain types; adapt framework/schema types at shell boundaries.

## Docstrings

- Write docstrings for public modules, classes, and functions using repository conventions and enforced linting/formatting rules.
- Keep docstrings focused on behavior and contract, not implementation trivia.
- Document caller-relevant semantics: invariants, side effects, and raised exceptions.
