# Releasing skills-mcp

`skills-mcp` is a **standalone Python package** living in a subdirectory of the [skills](https://github.com/ahgraber/skills) repo.
It is versioned and tagged **independently** of the agent-skills collection:

|                                  | Version source                       | Changelog                 | Tag prefix     | Cut with   |
| -------------------------------- | ------------------------------------ | ------------------------- | -------------- | ---------- |
| **skills-mcp** (this package)    | `pyproject.toml` `[project].version` | `skills-mcp/CHANGELOG.md` | `skills-mcp-v` | `uv-ship`  |
| skills collection (rest of repo) | none (doc collection)                | `../CHANGELOG.md`         | `skills-v`     | manual tag |

Releases are cut with [uv-ship](https://floraths.github.io/uv-ship/), a CLI that bumps
the version (via `uv version`), refreshes this changelog, then commits, tags, and pushes
in one step.

## Prerequisites

`uv-ship` is a developer tool, not a project dependency — install it once, user-wide:

```sh
uv tool install uv-ship
```

## Versioning model

The package uses a **static** `[project].version` in `pyproject.toml` (the uv default).
`uv-ship` drives `uv version` to bump it, which also updates `uv.lock`.
The runtime `skills_mcp.__version__` reads the installed metadata via `importlib.metadata`, so it can never drift from `pyproject.toml`.

> Do **not** switch to VCS/dynamic versioning (`dynamic = ["version"]`,
> `uv-dynamic-versioning`, etc.) — it is incompatible with the `uv version` / uv-ship
> bump flow, which requires an editable static version field.

Bump rules (SemVer): breaking API/CLI/behavior change → MAJOR, new capability → MINOR, fix → PATCH.

## Cutting a release

Run **from this directory** (`skills-mcp/`) so `uv version` targets this package, and
**always pass `--config pyproject.toml`** (see the gotcha below):

```sh
cd skills-mcp

# 1. Preview the changelog section built from commits since the last skills-mcp-v* tag
uv-ship --config pyproject.toml log --latest

# 2. Dry-run the release: shows the bump, changelog, commit, tag, and push
uv-ship --config pyproject.toml --dry-run next minor

# 3. Cut it: bump pyproject.toml + uv.lock, refresh CHANGELOG.md, commit, tag, push
uv-ship --config pyproject.toml next minor
```

- `next {major|minor|patch}` computes the bump; `version <X.Y.Z>` sets an explicit version.
- `log --save` refreshes `CHANGELOG.md` without cutting a release.
- Every command accepts `--dry-run`.

> **Config gotcha.** Without `--config`, uv-ship infers its config path by walking up to
> the **git root** (`../`), which has no `[tool.uv-ship]` table — so it reports
> `config source: "default"`, ignores this package's `tag-prefix` / `commit-message` /
> `changelog-path`, and would tag `v…` instead of `skills-mcp-v…`. Passing
> `--config pyproject.toml` from this directory points it at this package's table.
> Verify with the dry-run: the changelog header should read `skills-mcp-v…` and
> `config source` should be `"pyproject.toml"`.

A clean working tree and the configured `release-branch` (`main`) are preflight-checked;
use `--dirty` only deliberately.

## Configuration

The `[tool.uv-ship]` table in `pyproject.toml`:

```toml
[tool.uv-ship]
release-branch = "main"                                    # releases are cut from main
tag-prefix = "skills-mcp-v"                                # distinct from the skills-v* series
commit-message = "bump(skills-mcp): {old_ver} → {new_ver}" # conventional, passes the commit hook
changelog-path = "skills-mcp/CHANGELOG.md"                 # repo-root-relative — MUST name this dir
allow-dirty = false                                        # releases require a clean tree
```

Two keys are load-bearing:

- **`tag-prefix`** — the default is `"v"`, which would collide with the skills collection's
  `skills-v*` scheme and confuse `git describe`. `skills-mcp-v` keeps this package's tags in
  their own namespace. (`git describe --match 'skills-mcp-v*'` resolves only this package.)
- **`changelog-path`** — uv-ship resolves it as `<repo-root>/<changelog-path>`, **not** relative to this directory.
  Naming `skills-mcp/CHANGELOG.md` keeps the changelog here instead of writing to the repo root.

## Sources

- [uv-ship documentation](https://floraths.github.io/uv-ship/)
- [`uv version`](https://docs.astral.sh/uv/guides/package/#updating-your-version)
