# `find-specs-roots.py` — output schema

The discovery script at `skills/sdd/scripts/find-specs-roots.py` emits a single JSON object on stdout.
The sdd skill consumes this to drive the **Locate Specs Root** dialogue.

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

   - `pointer.present` is false → use the candidate directory as `SPECS_ROOT`.
   - `pointer.malformed` is true → surface `pointer.malformed_reason` to the user.
     Do not silently fall back to the candidate directory.
   - `pointer.target_exists` is false → surface the broken pointer (`pointer.raw_target` → `pointer.resolved_target`) to the user.
     Do not silently fall back.
   - `pointer.target_shape_ok` is false → surface `pointer.target_shape_reason` to the user as a misconfigured pointer.
     Do not proceed with a target that is clearly not an SDD root.
   - `pointer.target_outside_workspace` is true → announce the marker, the absolute target, and that the redirect leaves the workspace; ask the user to confirm before proceeding.
   - `pointer.extra_lines_ignored` is true → announce that extra lines in the pointer were ignored so the user can fix the format.
     Continue resolution.
   - Otherwise → use `pointer.resolved_target` as `SPECS_ROOT`.
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

For users authoring or reviewing the file:

- Plain text, UTF-8.
- Blank lines and lines starting with `#` are ignored.
- The first remaining line is the target path.
- Absolute paths (`/...`) and `~/...` are accepted; relative paths resolve relative to the directory containing the `SPECS_ROOT` file.
- The pointer lets a repo keep a discoverable `.specs/` marker at the project root while the real spec tree lives elsewhere (e.g., a sibling docs repo, a monorepo package, or a non-hidden directory).

## Top-level fields

| Field                       | Type                           | Notes                                                                                   |
| --------------------------- | ------------------------------ | --------------------------------------------------------------------------------------- |
| `anchor_path`               | string                         | Absolute path to the workspace anchor used for all discovery and boundary checks.       |
| `anchor_source`             | `"git" \| "cwd" \| "override"` | How the anchor was determined.                                                          |
| `explicit`                  | object \| null                 | Present only when `--explicit` was passed. See **Explicit** below.                      |
| `dot_specs_candidates`      | array                          | All `.specs/` directories found under the anchor. Empty when `--explicit` was passed.   |
| `specs_fallback_candidates` | array                          | Plausible non-hidden `specs/` directories. Populated only when `fallback_used` is true. |
| `fallback_used`             | boolean                        | True when no `.specs/` was found and the script ran the `specs/` fallback.              |

Discovery skips common build/dependency directories (`.git`, `node_modules`, `.venv`, `venv`, `vendor`, `dist`, `build`, `.nox`, `.tox`, `target`, `site-packages`, `__pycache__`).
The `specs/` fallback is depth-limited to 4 levels under the anchor.

## Explicit

```jsonc
{
  "raw": "./services/auth",                  // exactly what the user passed
  "resolved": "/abs/path/services/auth",     // resolved + tilde-expanded
  "exists": true,
  "outside_workspace": false                 // true when resolved path is not under anchor
}
```

When `explicit` is set, `dot_specs_candidates` and `specs_fallback_candidates` are always empty.
The skill must not follow any `SPECS_ROOT` pointer file at the explicit path — explicit user paths are final.

## DotSpecsCandidate

```jsonc
{
  "path": "/abs/path/.specs",
  "pointer": { ... } | null   // null only when no SPECS_ROOT file existed at all
}
```

Note: `pointer` is non-null whenever a `SPECS_ROOT` file is _present_ — even if it's malformed.
Use `pointer.present` (always `true` in that case) to distinguish "no pointer file" (the field would be `null`) from "pointer present but unusable" (`pointer.malformed` etc.).

### PointerInfo

| Field                      | Type           | Notes                                                                                               |
| -------------------------- | -------------- | --------------------------------------------------------------------------------------------------- |
| `present`                  | boolean        | Always `true` when this object is populated; `false` only via the surrounding `null`.               |
| `raw_target`               | string \| null | First non-comment line of the pointer file. `null` if malformed.                                    |
| `resolved_target`          | string \| null | Absolute resolved path of `raw_target`. `null` if malformed.                                        |
| `malformed`                | boolean        | True when the pointer file has no non-comment line, or could not be read.                           |
| `malformed_reason`         | string \| null | Human-readable reason (e.g., `"no non-comment line in pointer file"`).                              |
| `extra_lines_ignored`      | boolean        | True when the pointer file had more than one non-comment line; the first was used.                  |
| `target_exists`            | boolean        | Filesystem existence check for `resolved_target`.                                                   |
| `target_is_dir`            | boolean        | True when the target is a directory.                                                                |
| `target_outside_workspace` | boolean        | True when the resolved target lies outside the workspace anchor.                                    |
| `target_shape_ok`          | boolean        | True when the target is empty (freshly initialized) **or** contains `specs/`/`changes/`/`schemas/`. |
| `target_shape_reason`      | string \| null | Reason when `target_shape_ok` is false.                                                             |

The script follows pointers **at most once**.
If the resolved target itself contains a `SPECS_ROOT` file, it is ignored — the script does not chase pointers transitively.

## SpecsFallbackCandidate

```jsonc
{
  "path":   "/abs/path/services/auth/specs",   // the specs/ directory itself
  "parent": "/abs/path/services/auth"          // parent — the SDD-layout default for SPECS_ROOT
}
```

The skill should default to offering `parent` as `SPECS_ROOT` (since the SDD layout places `specs/` alongside `changes/` and `schemas/`), with `path` as a secondary option for users who want the `specs/` directory itself.
The pointer-file check does not apply to fallback candidates.

## Examples

**No specs anywhere** (fresh repo):

```json
{
  "anchor_path": "/abs/repo",
  "anchor_source": "git",
  "explicit": null,
  "dot_specs_candidates": [],
  "specs_fallback_candidates": [],
  "fallback_used": true
}
```

→ Ask the user where to initialize `.specs/`.

**One `.specs/` with a valid in-workspace pointer**:

```json
{
  "anchor_path": "/abs/repo",
  "anchor_source": "git",
  "explicit": null,
  "dot_specs_candidates": [
    {
      "path": "/abs/repo/.specs",
      "pointer": {
        "present": true,
        "raw_target": "../docs/.specs",
        "resolved_target": "/abs/repo/../docs/.specs",
        "malformed": false,
        "malformed_reason": null,
        "extra_lines_ignored": false,
        "target_exists": true,
        "target_is_dir": true,
        "target_outside_workspace": false,
        "target_shape_ok": true,
        "target_shape_reason": null
      }
    }
  ],
  "specs_fallback_candidates": [],
  "fallback_used": false
}
```

→ Use `resolved_target` as `SPECS_ROOT`; announce both marker and target.

**`specs/` fallback hits both real and false-positive matches**:

```json
{
  "anchor_path": "/abs/repo",
  "anchor_source": "git",
  "explicit": null,
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
