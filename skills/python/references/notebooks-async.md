# Async in Notebooks (`.ipynb` and `#%%` `.py`)

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Outcome

Notebook workflows remain async-safe and reproducible without event-loop patching.

## File Format Policy

- Prefer `#%%` `.py` notebooks for reviewability, diffs, and normal Python tooling.
- Use `.ipynb` when rich notebook metadata/output is explicitly required.
- Keep reusable logic in importable modules; notebook cells should orchestrate and inspect.

## Event Loop Ownership

- In IPython/Jupyter/VS Code notebooks, treat the event loop as host-owned.
- Use top-level `await` in cells for coroutine entry.
- Do not call `asyncio.run()`, `loop.run_until_complete()`, or `loop.run_forever()` in notebook cells.
- Use `asyncio.gather(...)` for notebook fan-out when all subtasks should complete before the next step.

## Library Module Rules

- In shared library modules, expose `async def` APIs and let callers decide how to run them.
- Do not call `asyncio.run()` inside library functions or reusable module internals.
- If a sync entrypoint is needed, keep it at the CLI/app boundary only.

## Background Work Pattern

- Use `asyncio.create_task()` for concurrent/background work and keep task handles.
- Cancel tasks explicitly when stopping work.
- Await cancellation completion (for example with `asyncio.gather(..., return_exceptions=True)`).
- Prefer `TaskGroup` when all concurrent tasks are owned by a single scoped operation.

## Script + Notebook Compatibility

```python
import asyncio


async def main():
    ...


def run():
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(main())  # script path
    else:
        return asyncio.create_task(main())  # notebook path
```

- Script usage: call `run()`.
- Notebook usage: `task = run(); await task`.

## Interop with Loop-Owning or Blocking Libraries

- Prefer async-native APIs when available.
- If a sync wrapper blocks or tries to own the loop, isolate it with `await asyncio.to_thread(...)`.
- Use a separate process when thread isolation is insufficient (heavy CPU or hard runtime isolation needs).

## Async Context Managers Across Cells

- Prefer wrapping the full lifecycle in one async function and `await`ing it from a single cell.
- Avoid manual `__aenter__`/`__aexit__` calls across many cells unless you also own explicit cleanup discipline.
- If you must manually enter/exit, pair entry/exit with `try/finally` so interrupted notebook flow does not leak resources.

## `nest_asyncio` Policy

- `nest_asyncio` is archived/unmaintained; do not add it as a default dependency.
- Prefer boundary adaptation (top-level `await`, async APIs, `to_thread`, process isolation) over loop patching.
- Treat loop patching as a temporary legacy workaround only.

## Notebook Environment Notes

- VS Code notebooks use `ipykernel`; the same running-loop constraints apply.
- `%gui asyncio` is for widget/GUI event-loop integration scenarios, not a default requirement for normal async I/O.
