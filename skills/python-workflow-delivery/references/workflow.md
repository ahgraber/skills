# Setup and Workflow

## Outcome

A predictable branch-to-PR workflow that is reproducible locally and in CI.

## Workflow Stages

1. Prepare environment and dependencies.
2. Create a branch with a task-focused name.
3. Implement the smallest vertical slice that proves behavior.
4. Run validation gates and resolve failures.
5. Update tests/docs/contracts when behavior or interfaces change.
6. Open PR with risk notes and validation summary.

## Baseline Guardrails

- Use project-defined Python version first.
- Use `uv` for environment and dependency workflow.
- Run Python tooling via `uv run ...` (or an explicitly activated project virtual environment).
- Prefer `#%%` `.py` notebooks over `.ipynb` unless `.ipynb` is explicitly required.

## Validation Gate (Before Review)

- Refresh environment after dependency or lockfile changes:
  - `uv sync`
- Use reproducibility parity checks when needed (typically pre-review/CI parity):
  - `uv sync --locked`
  - `uv lock --check`
- Required quality checks for review-ready scope:
  - `uv run ruff check .`
  - `uv run ruff format --check .`
  - `uv run pytest`
- Additional suites for relevant change types:
  - Dependency/lockfile changes:
    - `uv run pytest scripts/test_pypi_security_audit.py -v`
  - Async/concurrency lifecycle changes:
    - Run `pyleak` diagnostics on representative async integration tests.
- If a check fails, fix root causes and re-run affected checks before running the full gate again.

## PR Readiness

- New behavior and regression paths are tested.
- Lockfile state is intentional (no accidental drift).
- PR description includes:
  - problem statement
  - scope and non-goals
  - behavior changes
  - reliability considerations (timeouts/retries/idempotency, if relevant)
  - test evidence
