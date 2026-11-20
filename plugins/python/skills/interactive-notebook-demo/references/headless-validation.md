# Headless validation of a `#%%` demo notebook

The committed `.py` percent-file is the artifact, and its top-level `await`s are the part most likely to break interactively.
Validate **that file**, executed through a real Jupyter kernel — not a rewritten copy.

## The trap to avoid

Do **not** validate by wrapping the cells in `async def main(): ...` + `asyncio.run(main())` and running `python file.py`.
That executes a _different_ program (function-scoped awaits, a script guard) and leaves the actual top-level-await artifact unverified.
A reviewer's job is to catch exactly this substitution.
The same applies to any `if __name__ == "__main__"` script-mode path — straight-line `python` execution is not how the notebook is used.

## Run the real file through a live kernel

Use jupytext to convert-and-execute the percent-file against a registered ipykernel, writing the executed notebook to a throwaway location.
Never commit the generated `.ipynb`.

```bash
# Sandbox-safe: redirect all Jupyter/IPython state into $TMPDIR
export JUPYTER_CONFIG_DIR="$TMPDIR/jcfg" JUPYTER_DATA_DIR="$TMPDIR/jdata" \
       JUPYTER_RUNTIME_DIR="$TMPDIR/jrun" IPYTHONDIR="$TMPDIR/ipy" \
       JUPYTER_PATH="$TMPDIR/kprefix/share/jupyter" \
       JUPYTER_NO_MIGRATE=1 JUPYTER_PLATFORM_DIRS=1
mkdir -p "$JUPYTER_CONFIG_DIR" "$JUPYTER_DATA_DIR" "$JUPYTER_RUNTIME_DIR" "$IPYTHONDIR"

uv run --with jupytext --with nbclient --with ipykernel bash -c '
  python -m ipykernel install --prefix "$TMPDIR/kprefix" --name demo >/dev/null 2>&1
  jupytext --to ipynb --execute --set-kernel demo \
    notebooks/01_tour.py -o "$TMPDIR/nb01.ipynb"
'
```

Registering a project-scoped kernel with `--set-kernel` avoids the "no kernel named python3" failure you hit when only the bare `ipykernel` wheel is present.

## Assert it actually ran clean

```bash
jq '[.cells[]|select(.cell_type=="code")]|length'                                "$TMPDIR/nb01.ipynb" | xargs echo "code cells:"
jq '[.cells[]|select(.cell_type=="code")|select(.execution_count==null)]|length' "$TMPDIR/nb01.ipynb" | xargs echo "unexecuted:"
jq '[.cells[].outputs[]?|select(.output_type=="error")]|length'                  "$TMPDIR/nb01.ipynb" | xargs echo "error outputs:"
```

Pass criteria: **unexecuted = 0** and **error outputs = 0**.
If any optional-dependency cells exist (e.g. a sandbox/execution feature), confirm they actually ran when the dependency is installed — they are the easiest to silently skip.

Note what this does and doesn't catch: error-count = 0 proves nothing _crashed_, not that the values were _right_.
That is why evidence cells should `assert` their invariants (see SKILL.md principle 5) — a wrong value then raises, fails this run, and the same command run in CI becomes a real regression gate against drift, not just a smoke test.

Spot-check that the evidence cells produced the data they promise:

```bash
jq -r '.cells[].outputs[]?|.text[]?' "$TMPDIR/nb01.ipynb" | rg -i 'revision|before|after|<a value the markdown promises>'
```

For infra-dependent notebooks you cannot start services for, validate the **probe path** instead: run the first cell's logic without the stack and confirm it prints the actionable message with no traceback (exit 0).

## Ruff per-file-ignores for percent notebooks

The percent format trips lint rules that are wrong for notebooks.
Add a scoped per-file-ignore for the notebook glob rather than littering `# noqa` — match where the project keeps ruff config (`.ruff.toml` or `pyproject.toml`):

```toml
[per-file-ignores]
"notebooks/*" = [
  "F704", # `await` outside an async function — valid as top-level await in cells
  "E402", # module-level import not at top — later setup cells import on demand
  "B018", # useless expression — a bare value in a cell is its displayed output
  "D",    # docstrings — demo cells are prose-in-markdown, not docstrings
  "S",    # asserts / demo-grade security shortcuts
]
```

Keep `uv run ruff check notebooks/` clean.

## Repo hygiene checklist

- **Never commit the executed `.ipynb`** — it is a validation byproduct.
  The `#%%` `.py` is the source of truth.
- **`.gitignore`** the demo artifacts (local DB files, data/temp dirs the notebook creates).
- **`README.md`** for the notebooks dir: how to open in VS Code/Jupyter, how to start the demo stack, and a port table.
- **Delete scratch.**
  Remove any temporary validation scripts or `_scratch/` dirs before finishing — leave nothing behind.
