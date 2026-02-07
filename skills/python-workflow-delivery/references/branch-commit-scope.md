# Branch, Commit, and Scope Discipline

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

Small, reviewable changes that are easy to reason about and easy to revert.

## PR Scope Rules

- Keep each PR focused on one change objective.
- Prefer separate PRs for behavior changes vs. refactors.
- If mixed changes are unavoidable, isolate behavior and refactor work in separate commits.
- Avoid broad file churn unrelated to the task.

## Branch Naming

- Use task-focused branch names that communicate intent.
- Follow repository branch naming conventions when defined.
- If no convention exists, choose a consistent pattern (for example `feat/<area>-<intent>`, `fix/<area>-<issue>`, `refactor/<area>-<intent>`).
- Avoid ambiguous names such as `update` or `changes`.

## Commit Quality

- Keep commits logically grouped and revert-friendly.
- Ensure each commit leaves the repo in a coherent state.
- Write commit messages that describe observable behavior impact when present.
- Do not hide behavior changes inside "cleanup" commits.
