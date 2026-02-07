# Consistency Boundaries and Cross-Module State

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

Strong local consistency with resilient cross-module workflows.

## Immediate Consistency Rules

- Treat each module as the unit of immediate consistency.
- Keep transactions scoped to a single module boundary.
- Enforce module invariants before publishing side effects.

## Cross-Module Workflow Rules

- Do not span transactions across module boundaries.
- Coordinate via events, queued commands, or background jobs.
- Design cross-module flows for eventual consistency by default.

## Request-Path Interaction Rules

- During request handling, avoid synchronous domain call chains across services/modules.
- Allow orchestration-only interactions: publish events, enqueue jobs, or call infrastructure services.
- Keep business decisions in the handling module's core logic.
