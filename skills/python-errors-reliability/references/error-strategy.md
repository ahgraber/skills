# Error Strategy

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

Failures are actionable by code and diagnosable by humans.

## Error Model

- Design errors for two audiences: machine recovery and human debugging.
- Design errors for caller action, not origin labels.
- Prefer specific exception types over generic exceptions.
- Encode actionable metadata (`kind`, `retryable`, status/code, context).
- Keep external error categories stable across internal refactors.
- Avoid leaking provider internals across module boundaries.

## Boundary Handling

- Catch exceptions only where recovery or translation is possible.
- Keep `try` blocks narrow to isolate the intended failure scope.
- Translate exceptions at module boundaries and preserve cause with `raise ... from ...`.
- Re-raise with operation context (what failed, for which entity, in which phase).
- Never swallow failures silently.

## Logging Discipline

- Log once per failed operation at a meaningful boundary.
- Avoid duplicate logs for the same failure path.
- Include operation ID, phase, and safe diagnostic context.
- Use `logger.exception(...)` or `exc_info=True` when recording failure boundaries.
- Use `%`-style logging argument interpolation for structured logging compatibility.
- Keep logging in imperative shell/integration layers, not pure core logic.

## Public Contract Rules

- Document failure modes and retryability expectations for public interfaces.
- For batch operations, return per-item outcomes unless atomic all-or-nothing behavior is required.
- Do not parse exception message strings for control flow; use typed fields or error kinds.
