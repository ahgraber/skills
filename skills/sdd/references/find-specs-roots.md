# `find-specs-roots.py` — output schema

The discovery script at `skills/sdd/scripts/find-specs-roots.py` emits a single JSON object on stdout.
The sdd skill consumes this to drive the **Locate Specs Root** dialogue.

## What is a SPECS_ROOT?

A **SPECS_ROOT** is a directory whose direct children conform to the SDD layout: `specs/`, `changes/`, and `schemas/` (with optional `.sdd/`).
The conventional location is a hidden `.specs/` at a project root; in a monorepo, each package may have its own `<package>/.specs/`.

## Invocation

```sh
skills/sdd/scripts/find-specs-roots.py [--explicit PATH] [--workspace PATH]
```

- `--explicit PATH` — user-supplied path.
  When set, the script analyzes only this path and skips discovery.
- `--workspace PATH` — override the workspace anchor.
  Defaults to `git rev-parse --show-toplevel`, falling back to the cwd when not inside a git repo.

## Decision branches

Read these fields off the script's JSON to drive the **Locate Specs Root** dialogue:

1. `explicit` is set → use `explicit.resolved` as `SPECS_ROOT` directly.
   **Do not follow a `SPECS_ROOT` pointer** even if one exists there — an explicit user path is final.
   If `explicit.outside_workspace` is true, announce the absolute path and ask the user to confirm before proceeding.
   If `explicit.exists` is false, ask whether to initialize there.

2. `dot_specs_candidates` has multiple entries → list them (showing each entry's pointer status and target) and ask which to use.
   Then proceed to step 3 with the chosen candidate.

3. `dot_specs_candidates` has one entry (or one was just chosen) → handle its `pointer` field:

   - `pointer` is `null` → no `SPECS_ROOT` file; use the candidate directory as `SPECS_ROOT`.
   - `pointer.malformed` is true:
     - `malformed_reason` is `"empty"` → tell the user the file has no valid entries and show the expected format.
     - `malformed_reason` is `"unreadable"` → tell the user the file could not be read; show `malformed_detail` (the OS error) and ask them to check permissions or encoding.
       Do not silently fall back in either case.
   - `pointer.targets` has multiple entries → list them (showing each entry's `raw` path and `comment` if present) and ask which to use.
     Then apply the single-target rules below to the chosen entry.
   - `pointer.targets` has one entry → apply the single-target rules:
     - `target.exists` is false → surface the broken pointer (`target.raw` → `target.resolved`) to the user.
       Do not silently fall back.
     - `target.is_dir` is false → surface that the target is a file, not a directory; do not proceed.
     - `target.outside_workspace` is true → announce the marker, the absolute target, and that the redirect leaves the workspace; ask the user to confirm before proceeding.
     - Otherwise, before using `target.resolved` as `SPECS_ROOT`, run an agent-side filesystem check: if the target directory has no `specs/`, `changes/`, or `schemas/` subdirectory **and** contains a `.specs/` subdirectory, the pointer almost certainly names the _parent_ of `.specs/` instead of a SPECS_ROOT.
       Surface the mismatch, name the likely intended target (`<target>/.specs`), and ask the user to fix the manifest before proceeding.
       If the check passes (or doesn't trigger), use `target.resolved` as `SPECS_ROOT`.
   - The pointer is followed at most once.
     The script does not chase pointers transitively, and neither should the agent.

4. `dot_specs_candidates` is empty and `fallback_used` is true → handle `specs_fallback_candidates`:

   - Empty → ask the user where to initialize `.specs/` (default: repo root).
   - One or more entries → list them and ask the user, for each candidate, whether to use the **parent** of `specs/` (the `parent` field; default — matches the SDD layout where `specs/` sits alongside `changes/`, `schemas/`), the `specs/` directory itself (the `path` field), or none (then ask where to initialize).
     Note that `specs/` is also commonly used for test fixtures, OpenAPI/JSON schemas, or RSpec — the user is the disambiguator.
     The pointer-file check does **not** apply to `specs/` fallback candidates; a non-hidden `specs/` directory is not a marker.

**Announce the resolved `SPECS_ROOT` in all cases** — whether it came from an explicit user path, a `.specs/` candidate, the `specs/` fallback, or a pointer redirect.
If a pointer was followed, also announce the marker and target so the user can confirm.

## `SPECS_ROOT` pointer-file format

A `SPECS_ROOT` file is a **manifest of SPECS_ROOT directories** (see definition at the top of this document).
Each non-comment line names one SPECS_ROOT; targets are used as-is, never auto-drilled.

For users authoring or reviewing the file:

- Plain text, UTF-8.
- Blank lines and lines starting with `#` are ignored.
- Each remaining line is a target path naming a SPECS_ROOT directory.
  A single entry redirects to one spec root; multiple entries let the agent ask which to use (same UX as discovering multiple `.specs/` directories).
- Trailing `#` and `//` comments (space-prefixed) are stripped from each target line before resolution.
  Whichever marker appears earliest in the line wins.
- Absolute paths (`/...`) and `~/...` are accepted; relative paths resolve relative to the directory containing the `SPECS_ROOT` file.
- The pointer lets a repo keep a discoverable `.specs/` marker at the project root while the real spec tree lives elsewhere (e.g., a sibling docs repo, a monorepo package, or a non-hidden directory).
  In a monorepo, list one `.specs/` path per project to consolidate the manifest.

_Compat:_ before the current format, only the first non-comment line was used as the target.
Old pointer files with stray trailing lines (previously silently ignored) are now treated as multi-entry manifests — clean them up if that is not intended.

### Agent-write convention

When an agent writes or updates a `SPECS_ROOT` file, the file MUST begin with a top-level header comment that names the manifest's purpose, e.g.:

```text
# Manifest of available specs roots — each line is a <project>/.specs/ directory.
```

The header is documentation for the next human or agent who opens the file; it prevents the recurring confusion of pointing at a _parent_ of `.specs/` instead of the `.specs/` directory itself.

## Output schema

Top-level JSON fields:

| Field                       | Type                           | Notes                                                                                                                         |
| --------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------------------------- |
| `anchor_path`               | string                         | Absolute path to the workspace anchor used for all discovery and boundary checks.                                             |
| `anchor_source`             | `"git" \| "cwd" \| "override"` | How the anchor was determined.                                                                                                |
| `explicit`                  | `ExplicitPath \| null`         | Present only when `--explicit` was passed. When set, `dot_specs_candidates` and `specs_fallback_candidates` are always empty. |
| `dot_specs_candidates`      | `DotSpecsCandidate[]`          | All `.specs/` directories found under the anchor. Empty when `--explicit` was passed.                                         |
| `specs_fallback_candidates` | `SpecsFallbackCandidate[]`     | Plausible non-hidden `specs/` directories. Populated only when `fallback_used` is true.                                       |
| `fallback_used`             | boolean                        | True when no `.specs/` was found and the script ran the `specs/` fallback.                                                    |

Nested types:

```ts
ExplicitPath           = { raw: string; resolved: string; exists: bool; outside_workspace: bool }
DotSpecsCandidate      = { path: string; pointer: PointerInfo | null }
PointerInfo            = { malformed: bool; malformed_reason: "unreadable" | "empty" | null;
                           malformed_detail: string | null; targets: TargetInfo[] }
TargetInfo             = { raw: string; comment: string | null; resolved: string;
                           exists: bool; is_dir: bool; outside_workspace: bool }
SpecsFallbackCandidate = { path: string; parent: string }
```

Notes:

- `outside_workspace` is true when the resolved path lies outside `anchor_path`.
- `is_dir` is only meaningful when `exists` is true.
- `pointer` is `null` when no `SPECS_ROOT` file exists at the candidate directory; it is populated even if the file is malformed.
- The script follows pointers **at most once** — if a resolved target itself contains a `SPECS_ROOT` file, it is ignored.
- For `SpecsFallbackCandidate`, `parent` is the SDD-layout default to offer as `SPECS_ROOT`; `path` is the `specs/` directory itself.
- Discovery skips common build/dependency directories (`.git`, `node_modules`, `.venv`, `venv`, `vendor`, `dist`, `build`, `.nox`, `.tox`, `target`, `site-packages`, `__pycache__`).
  The `specs/` fallback is depth-limited to 4 levels under the anchor.

## Examples

Each example shows only the fields that distinguish that branch; omitted fields take their default/empty values.

**No specs anywhere** (fresh repo) — `dot_specs_candidates: []`, `specs_fallback_candidates: []`, `fallback_used: true`.
→ Ask the user where to initialize `.specs/`.

**One `.specs/` with a valid in-workspace pointer (single target)**:

```json
{
  "dot_specs_candidates": [
    {
      "path": "/abs/repo/.specs",
      "pointer": {
        "targets": [
          {
            "raw": "../docs/.specs",
            "resolved": "/abs/docs/.specs",
            "exists": true,
            "is_dir": true,
            "outside_workspace": false
          }
        ]
      }
    }
  ]
}
```

→ Use `targets[0].resolved` as `SPECS_ROOT`; announce both marker and target.

**Multi-entry pointer (monorepo manifest)** — `pointer.targets` contains both `../packages/api/.specs` (resolved `/abs/repo/packages/api/.specs`) and `../packages/frontend/.specs` (resolved `/abs/repo/packages/frontend/.specs`).
→ List both targets and ask which to use.

**`specs/` fallback hits real and false-positive matches**:

```json
{
  "dot_specs_candidates": [],
  "specs_fallback_candidates": [
    {
      "path": "/abs/repo/services/auth/specs",
      "parent": "/abs/repo/services/auth"
    },
    {
      "path": "/abs/repo/tests/specs",
      "parent": "/abs/repo/tests"
    }
  ],
  "fallback_used": true
}
```

→ Ask the user which (if any) is the spec root; `tests/specs` is likely test fixtures.
