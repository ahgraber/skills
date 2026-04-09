# Free-Threaded Python Testing

## Outcome

Code is validated for thread safety under free-threaded CPython (GIL-disabled builds), catching race conditions, C extension incompatibilities, and shared-state corruption that the GIL previously masked.

## When to Apply

- Library or application targeting free-threaded Python builds.
- Code with shared mutable state accessed from multiple threads.
- C extensions or projects depending on C extensions.
- Adding free-threaded Python to an existing CI matrix.
- Investigating flaky failures that only appear under concurrent execution.

## Background

**PEP 703** introduced an optional GIL-disabled build (experimental in 3.13).
**PEP 779** promoted it to officially supported (3.14+).
The roadmap targets a single ABI with runtime GIL control, then GIL disabled by default.

Free-threaded builds use the `t` suffix (e.g., `3.13t`, `3.14t`) and a corresponding ABI tag (`cp313t`, `cp314t`).

Identify build type at runtime:

```python
import sys, sysconfig

sys._is_gil_enabled()  # False if GIL disabled
sysconfig.get_config_var("Py_GIL_DISABLED")  # 1 for free-threaded build
```

Runtime GIL control:

```bash
python3.Xt script.py              # GIL disabled by default in free-threaded builds
PYTHON_GIL=0 python3.Xt script.py # Force GIL disabled (even if extensions request it)
PYTHON_GIL=1 python3.Xt script.py # Force GIL re-enabled
python3.Xt -X gil=1 script.py     # Same via CLI flag
```

## Why the GIL Masked Bugs

The GIL serialized all bytecode execution, hiding:

- **Race conditions on shared mutable state**: `counter += 1` spans multiple bytecodes and is not atomic without the GIL.
- **Unsafe global state**: Module-level dicts, class caches, singletons that relied on implicit serialization.
- **C extension thread unsafety**: Extensions assuming the GIL provided mutual exclusion can now segfault or corrupt data.
- **Reference counting issues**: Free-threaded builds use per-object locking and biased refcounting; borrowed references in C code can cause use-after-free.
- **Silent GIL re-enablement**: Importing a C extension without `Py_mod_gil` declaration causes the runtime to re-enable the GIL, silently negating parallelism.

## Installing Free-Threaded Python

```bash
uv python install 3.Xt
uv venv --python 3.Xt
```

Replace `3.Xt` with the desired version (free-threaded builds available from 3.13t onward; 3.14t+ recommended as the first officially supported release).

## Testing Strategy

### Phase 1: Baseline on GIL-enabled build

Run the existing test suite on the latest stable Python.
Fix any baseline failures before introducing free-threading.

### Phase 2: Stress-test with tiny switch interval

Expose latent thread-safety bugs even on GIL-enabled builds:

```python
import sys

sys.setswitchinterval(0.000001)  # 1 microsecond — forces more thread switching
```

### Phase 3: Add pytest-run-parallel

The primary community plugin (Quansight Labs).
Runs each test concurrently in a thread pool.

```bash
uv add --dev pytest-run-parallel

# Run each test in 5 parallel threads
pytest --parallel-threads=5

# Auto-detect thread count
pytest --parallel-threads=auto

# Skip known thread-unsafe tests
pytest --parallel-threads=5 --skip-thread-unsafe

# Run repeatedly to reproduce rare races
pytest --parallel-threads=5 --forever
```

Mark thread-unsafe tests:

```python
import pytest


@pytest.mark.thread_unsafe
def test_uses_global_state():
    """Cannot run in parallel — modifies module-level state."""
    ...


@pytest.mark.parallel_threads(10)
def test_high_contention():
    """Override thread count for this specific test."""
    ...
```

Declare thread-unsafe fixtures in config:

```ini
# pyproject.toml [tool.pytest.ini_options] or pytest.ini
thread_unsafe_fixtures =
    fixture_using_global_state
    my_monkeypatch_fixture
```

Auto-skip flags: `--mark-warnings-as-unsafe`, `--mark-ctypes-as-unsafe`, `--mark-hypothesis-as-unsafe`.

### Phase 4: Run on free-threaded build

```bash
PYTHON_GIL=0 uv run --python 3.Xt pytest --parallel-threads=auto --timeout=300
```

### Phase 5: Repeat for flaky failures

Race conditions are non-deterministic.
Use `pytest-repeat` to increase reproduction probability:

```bash
PYTHON_GIL=0 uv run --python 3.Xt pytest -x -v --count=100 test_concurrent.py
```

## Writing Explicit Multithreaded Tests

Use `threading.Barrier` to synchronize workers and maximize concurrent access at the suspected race point:

```python
import threading
from concurrent.futures import ThreadPoolExecutor


def test_concurrent_dict_access():
    shared = {}
    barrier = threading.Barrier(8)

    def worker(i):
        barrier.wait()  # all threads start simultaneously
        shared[f"key_{i}"] = i

    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(worker, i) for i in range(8)]
        for f in futures:
            f.result()

    assert len(shared) == 8
```

## Pytest Fixtures Known to Be Thread-Unsafe

These fixtures must not be used from parallel threads without protection:

- `capsys`, `capfd`, `capsysbinary`, `capfdbinary`, `capteesys` — capture is global.
- `tmp_path`, `tmpdir` — `pytest-run-parallel` patches these; without the plugin they share paths.
- `monkeypatch` — inherently modifies global state.
- `pytest.warns`, `pytest.deprecated_call`, `recwarn` — `warnings.catch_warnings` is not thread-safe prior to 3.14's `-X context_aware_warnings`.

The pytest maintainers have explicitly ruled out making pytest infrastructure itself thread-safe.
Tests can manage their own threads, but don't assume pytest internals are safe.

## Thread Sanitizer (TSan)

For C extensions and native code, TSan detects data races at runtime.

Build CPython with TSan:

```bash
CC=clang CXX=clang++ ./configure --disable-gil \
    --with-thread-sanitizer --with-pydebug && make -j
```

Run under TSan:

```bash
TSAN_OPTIONS="suppressions=suppressions.txt halt_on_error=1" \
    python -m pytest -s -x test_threaded.py
```

- Pass `-s` to pytest so TSan output is not captured.
- Create a suppressions file for known upstream issues.
- TSan adds significant overhead — run only threaded test subsets.
- AddressSanitizer (`--with-address-sanitizer`) catches memory safety issues triggered by multithreaded execution.

## C Extension Compatibility

Extensions must opt into free-threading via the `Py_mod_gil` slot:

```c
// Multi-phase init
static struct PyModuleDef_Slot module_slots[] = {
    {Py_mod_gil, Py_MOD_GIL_NOT_USED},
    {0, NULL}
};

// Single-phase init
#ifdef Py_GIL_DISABLED
PyUnstable_Module_SetGIL(module, Py_MOD_GIL_NOT_USED);
#endif
```

Cython: `# cython: freethreading_compatible = True`.

Without this declaration, importing the extension silently re-enables the GIL.
Detect this:

```python
import the_extension
import sys

assert not sys._is_gil_enabled(), "GIL re-enabled — extension is not free-threading compatible"
```

The community tracks ecosystem compatibility at `py-free-threading.github.io/tracking/`.

## CI Setup

### GitHub Actions

```yaml
jobs:
  test-free-threaded:
    runs-on: ${{ matrix.os }}
    timeout-minutes: 10  # free-threaded tests can hang on deadlocks
    strategy:
      fail-fast: false
      matrix:
        python-version: # quote versions: unquoted 3.10 parses as float 3.1
          - 3.X
          - 3.Xt
        os: [ubuntu-latest, macos-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv python install ${{ matrix.python-version }}
      - name: Force GIL disabled
        if: endsWith(matrix.python-version, 't')
        run: echo "PYTHON_GIL=0" >> "$GITHUB_ENV"
      - run: |
          uv run --python ${{ matrix.python-version }} python -VV
          uv run --python ${{ matrix.python-version }} python -c "import sys; print('GIL enabled:', sys._is_gil_enabled())"
      - run: uv run --python ${{ matrix.python-version }} pytest --timeout=300
```

Always set `timeout-minutes` on the job — free-threaded tests are more prone to deadlocks.
Also set pytest-level timeouts:

```toml
[tool.pytest.ini_options]
faulthandler_timeout = 600
```

### nox Integration

```python
import nox

nox.options.default_venv_backend = "uv|virtualenv"

STABLE_PYTHONS = ["3.12", "3.13", "3.14"]


@nox.session(python=STABLE_PYTHONS)
def tests(session: nox.Session) -> None:
    session.install(".[test]")
    session.run("pytest", *session.posargs)


@nox.session()
def tests_freethreaded(session: nox.Session) -> None:
    """Run with free-threaded Python and parallel threads."""
    session.install(".[test]", "pytest-run-parallel")
    session.run(
        "pytest",
        "--parallel-threads=5",
        "--timeout=300",
        *session.posargs,
        env={"PYTHON_GIL": "0"},
    )
```

Run with the free-threaded interpreter: `nox -s tests_freethreaded --force-python python3.Xt`.

## Concurrent Data Structures

The `ft_utils` library (Meta/Facebook, MIT license) provides lock-free thread-safe primitives:

```python
from ft_utils import AtomicInt64, ConcurrentDict

counter = AtomicInt64(0)
counter.fetch_add(1)  # safe from multiple threads without locking

d = ConcurrentDict()  # scalable thread-safe dictionary
```

Works on both GIL-enabled and free-threaded builds.
Useful for replacing ad-hoc locking in hot paths.

## Common Pitfalls

- **Assuming built-in ops are atomic**: `dict[k] = v` and `list.append(x)` are not guaranteed atomic without the GIL.
  Use `threading.Lock` or `ft_utils` types.
- **Sharing iterators across threads**: Iterators are not thread-safe.
  Never pass an iterator to multiple threads.
- **Ignoring GIL re-enablement**: Check `sys._is_gil_enabled()` after all imports to confirm the GIL stayed off.
- **No CI timeout**: Free-threaded tests can deadlock.
  Always set both job-level and test-level timeouts.
- **Testing only once**: Race conditions may not reproduce on a single run.
  Use `--count=100` or `--forever` with `pytest-run-parallel`.
- **Skipping `monkeypatch` consideration**: `monkeypatch` modifies global state and is inherently thread-unsafe.
  Structure tests to avoid it in parallel contexts.
