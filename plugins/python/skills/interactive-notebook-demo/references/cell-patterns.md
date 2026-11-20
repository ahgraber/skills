# Cell patterns for interactive demo notebooks

Copy-paste skeletons.
The examples use a hypothetical async `store` client with pydantic-style models; swap in your own library's names and read the real method signatures before writing calls — use kwargs.
The prose in these cells follows `antislop-writing`: relevance lives in the first sentence, headings state a claim, and there are no `**Why this:**`-style meta-labels.

## Header cell

Lead with the problem the library solves, then the few terms the reader needs, then how to run it — all as prose, no label prefixes.

```python
# %% [markdown]
# # <Library> — a guided tour
#
# <Library> exists because <the concrete pain it removes — one or two sentences a
# newcomer actually feels, not abstract benefits>. This notebook walks the core
# operations end to end: run a cell, read its output, change a value, run it again.
#
# A few terms used throughout:
# - **<term>** — <one-line definition>.
# - **<term>** — <one-line definition>.
# It deliberately does not <non-goal>, which is why <consequence>.
#
# Step through top to bottom in **VS Code Interactive** or **Jupyter** — the kernel
# owns the event loop, so top-level `await` works in a cell (do not call
# `asyncio.run()`). There is no script mode. Edit any input and re-run a cell to
# explore — git holds the original. Cells are safe to re-run unless marked
# `# not idempotent` (those mutate state each run; Restart→Run-All resets the
# notebook). The cells in <section> need <optional dependency>, installed with `uv`.
```

## Section opener

A heading that states the section's claim, then two sentences that make its relevance evident.
No `**Story:**` / `**Mechanism:**` labels — write the point, don't announce it.

```python
# %% [markdown]
# ## Updates create revisions — they don't overwrite
# Saving an existing key keeps the prior value and writes a new revision on top,
# so nothing is lost and you can always see what changed. Watch the revision
# number climb in the output below — that is the rule firing.
```

## Closing a section: point into the code

End a section with one sentence naming the real source, contract, and tests behind it, so the reader can jump from the demo into the repo.
A sentence, not a `**Where this lives:**` label.

```python
# %% [markdown]
# The code is in `src/<pkg>/store.py` (`create`, `update`, `get`); the contract
# lives in `<spec path>` and worked examples in `tests/<...>`.
```

## Setup stays a function; invoke it in its own cell

Setup boilerplate the reader does not need to inspect granularly may stay a function.
Everything after is flattened.

```python
# %%
async def setup(tmp_dir: str):
    store = Store(path=tmp_dir)  # local, no external services
    await store.connect()
    return store


# %%
tmp_dir = tempfile.mkdtemp(prefix="demo-")
store = await setup(tmp_dir)
```

## The unit: one markdown cell, then one operation cell

```python
# %% [markdown]
# ## Updates create revisions — they don't overwrite
# Saving an existing key keeps the prior value and writes a new revision on top.
# This is the canonical non-idempotent cell — every run adds a revision — so it
# carries a marker: re-run it to watch the number climb, Restart→Run-All to reset.

# %%
# not idempotent: re-running adds a revision
before = await store.get(key="greeting")  # created in an earlier cell
after = await store.update(key="greeting", value={"text": "hi"}, expected_revision=before.revision)
print(f"before: revision {before.revision}  value={before.value}")
print(f"after : revision {after.revision}  value={after.value}")
```

## Prove-with-data idioms

Show the evidence for every claim the markdown makes.

```python
# The whole returned object, when its shape itself teaches (skip if it's huge):
print(rec.model_dump_json(indent=2))

# Before and after, side by side — the values, not "updated":
print(f"before: {before.value}\nafter : {after.value}")

# An invariant: assert it with the values in the message, so a wrong value fails
# the kernel run instead of quietly printing False — and the reader sees the numbers.
rb = await store.get(key="greeting")
assert rb.revision == after.revision, (rb.revision, after.revision)
print(f"read-back revision {rb.revision} == write revision {after.revision}")

# Read back after a write and show what came back, proving it landed:
print("stored value:", (await store.get(key="greeting")).value)
```

## The error-demo cell (try/except only here)

Keep try/except for cells whose _point_ is the failure.
Drop it everywhere else.

```python
# %% [markdown]
# ## A stale write is rejected, not merged
# `expected_revision` is an optimistic-concurrency guard: if someone wrote since
# you last read, your update is refused so you cannot clobber their change. The
# rejected write changes nothing, so this cell is idempotent — re-run it freely.

# %%
try:
    await store.update(key="greeting", value={"text": "oops"}, expected_revision=1)  # stale on purpose
except ConflictError as e:
    print(f"ConflictError (expected): {e}")
```

## Connectivity-probe cell (infra-dependent notebooks)

First cell of a notebook that needs external services.
Actionable message, no traceback, when the stack is down.

```python
# %%
import socket


def _tcp_ok(host: str, port: int, timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout):
            return True
    except OSError:
        return False


services = {"postgres": ("localhost", 55432), "object-store": ("localhost", 59000)}
missing = [name for name, (h, p) in services.items() if not _tcp_ok(h, p)]
if missing:
    print(f"Demo stack not available: {', '.join(missing)} unreachable.")
    print("Start it with:  docker compose -f notebooks/docker-compose.yaml up -d")
    print("Ports are chosen to not collide with the test stack (see the compose file header).")
else:
    print("Demo stack reachable — later cells will connect.")
```

## Cleanup cell (final)

```python
# %% [markdown]
# ## Cleanup
# Run this when you are done to close the client and remove the demo's temp files.

# %%
await store.close()
shutil.rmtree(tmp_dir, ignore_errors=True)
```
