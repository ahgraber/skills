# Multi-Python Version Testing

## Outcome

Test suite runs reliably across all supported Python versions with consistent dependency resolution, fast feedback, and minimal CI configuration drift.

## When to Apply

- Library or framework that supports multiple Python versions.
- Dependency matrix testing (N Python versions x M dependency variants).
- CI pipeline that must validate compatibility before release.

## nox

nox uses a Python file (`noxfile.py`) for configuration, giving full programmatic control over test sessions.
It pairs naturally with uv as the virtual environment backend.

### Basic Configuration

```python
import nox

nox.options.default_venv_backend = "uv|virtualenv"


@nox.session(python=["3.11", "3.12", "3.13", "3.14"])
def tests(session: nox.Session) -> None:
    session.install("pytest")
    session.run("pytest", *session.posargs)


@nox.session(python="3.14")
def lint(session: nox.Session) -> None:
    session.install("ruff")
    session.run("ruff", "check", ".")


@nox.session(python="3.14")
def type_check(session: nox.Session) -> None:
    session.install("mypy")
    session.run("mypy", "src")
```

Running `nox --list` expands multi-Python sessions into individual entries: `tests-3.11`, `tests-3.12`, etc.

### Parametrize for Dependency Matrices

```python
@nox.session(python=["3.12", "3.13"])
@nox.parametrize("django", ["4.2", "5.0"])
def tests(session: nox.Session, django: str) -> None:
    session.install(f"django~={django}.0", "pytest")
    session.run("pytest")
```

Produces: `tests(django='4.2')-3.12`, `tests(django='4.2')-3.13`, `tests(django='5.0')-3.12`, `tests(django='5.0')-3.13`.

### Session Selection

```bash
nox                          # run all default sessions
nox -s tests                 # run all "tests" sessions (all Python versions)
nox -s tests-3.12            # run specific session
nox --python 3.12            # run all sessions defined for Python 3.12
nox -k "not lint"            # pytest-style keyword filtering
nox -t "my_tag"              # tag-based filtering
```

### Session Reuse

By default nox recreates virtualenvs every run.
Override for speed:

```python
@nox.session(reuse_venv=True)
def tests(session): ...
```

Or at the CLI: `nox -r` (reuse existing venvs).
For finer control, use `--reuse-venv=yes|no|always|never` at the CLI.
The decorator accepts `bool | None` only; `always`/`never` are CLI-only options that override per-session settings.

### Tags and Dependencies

```python
@nox.session(tags=["ci", "tests"])
def tests(session): ...


@nox.session(python=["3.11", "3.14"], requires=["tests-{python}"])
def coverage(session): ...
```

### Interpreter Download

nox can download missing Python interpreters automatically:

```bash
nox --download-python auto   # download if interpreter not found (default for all backends)
```

## uv Integration

### Built-in uv Backend

```python
nox.options.default_venv_backend = "uv|virtualenv"  # fallback if uv unavailable
```

Set globally or per-session with `venv_backend="uv"`.

### Lockfile-Based Installs

```python
@nox.session(venv_backend="uv")
def tests(session: nox.Session) -> None:
    session.run_install(
        "uv",
        "sync",
        "--extra=test",
        "--no-default-extras",
        f"--python={session.virtualenv.location}",
        env={"UV_PROJECT_ENVIRONMENT": session.virtualenv.location},
    )
    session.run("pytest", *session.posargs)
```

The two critical lines are `--python=` and `UV_PROJECT_ENVIRONMENT=` — they tell uv to use nox's managed environment.

### nox-uv Package

The `nox-uv` third-party package adds `uv_groups`, `uv_extras`, `uv_only_groups` parameters to the `@session` decorator for tighter dependency group integration:

```python
from nox_uv import session
import nox

nox.options.default_venv_backend = "uv"


@session(python=["3.11", "3.12", "3.13"], uv_groups=["test"])
def test(s: nox.Session) -> None:
    s.run("pytest")
```

## CI Patterns (GitHub Actions)

### YAML Version Quoting

Always quote Python version strings: `"3.10"` not `3.10`.
YAML interprets unquoted `3.10` as float `3.1`.

### Matrix + nox

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.11', '3.12', '3.13', '3.14']
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v5
      - run: uv python install ${{ matrix.python-version }}
      - run: uv tool install nox
      - run: nox --python ${{ matrix.python-version }}
```

nox's `--python` flag runs only sessions matching the given version, pairing naturally with GitHub Actions matrix strategy.

### nox GitHub Action (No Matrix Needed)

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: wntrblm/nox@2024.04.15
        with:
          python-versions: 3.11, 3.12, 3.13
      - run: nox
```

Installs all specified Python versions in one runner.

### Caching

Cache the `.nox` directory keyed on config file hashes and Python version.
For uv-based workflows, `astral-sh/setup-uv` provides built-in cache support.
Use `nox -r` (reuse venvs) in CI for speed.

## PEP 735 Dependency Groups

nox supports PEP 735 dependency groups from `pyproject.toml` via `nox-uv`:

```toml
[dependency-groups]
test = ["pytest>=8", "pytest-cov>=5"]
```

```python
from nox_uv import session


@session(uv_groups=["test"])
def tests(s): ...
```

Or manually with `uv sync --group test`.

## Common Pitfalls

### Interpreter discovery

Missing interpreters are silently skipped locally but error in CI.
Set `nox.options.error_on_missing_interpreters = True` for consistency.
Use `nox --download-python auto` or the uv backend for auto-download.

### Virtualenv reuse

Default is recreate every run.
Use `nox -r` in CI for speed.
Use `--reuse-venv=always|never` at the CLI for fine-grained control (the decorator takes `bool | None`).

### Dependency resolution across versions

Different Python versions resolve different dependency trees.
Test minimum versions with explicit lower-bound pins or `uv`'s `--resolution lowest` flag in nox sessions.

### Package build overhead

nox does not automatically reuse built wheels across sessions.
For large matrices, build the wheel once in a dedicated session and install it in test sessions to avoid repeated builds.

## Documentation Links

- [nox — Configuration & API](https://nox.thea.codes/en/stable/config.html)
- [nox — Command-line usage](https://nox.thea.codes/en/stable/usage.html)
- [nox — Tutorial](https://nox.thea.codes/en/stable/tutorial.html)
