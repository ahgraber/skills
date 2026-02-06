# Code Design and Readability

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

Code that is easy to reason about, modify, and test under change.

## Primary Rules

- Prefer explicit control flow and explicit data movement.
- Keep naming domain-first and keep functions narrowly purposeful.
- Keep module boundaries strict; avoid architectural leakage and shared "common/utils" dumping.
- Bias toward simple, golden-path implementations before adding defensive complexity.

## Reference Map

- `readability-and-complexity.md`
- `module-boundaries.md`
- `functional-core-shell.md`
- `refactor-guidelines.md`
