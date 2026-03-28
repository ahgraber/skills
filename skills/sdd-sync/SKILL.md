---
name: sdd-sync
description: |-
  Use when merging delta specs from a change into the main baseline specs. Triggers: "sync specs", "merge delta specs", "update main specs", "apply the spec changes", "sync the change".
---

# SDD Sync

Merge delta specs from a change directory into the main baseline specs.
Applies each delta marker intelligently, preserving existing content not mentioned in the delta.

> `SPECS_ROOT` is resolved by the `sdd` router before this skill runs.
> Replace `.specs/` with your project's actual specs root in all paths below.

## When to Use

- After `sdd-verify` passes — implementation is confirmed correct
- Ready to finalize the change and update the source-of-truth specs

## When Not to Use

- Delta specs don't exist for this change — nothing to sync
- Implementation isn't verified — run `sdd-verify` first

## Soft Gate

If no delta specs exist in `.specs/changes/<name>/specs/`, warn:

> "No delta specs to sync."

Stop unless the user confirms to proceed.

## Process

### Phase 1: Identify What to Sync

1. Confirm the active change (ask if multiple active changes exist)
2. List all delta spec files in `.specs/changes/<name>/specs/`
3. For each delta spec, identify the corresponding main spec in `.specs/specs/`

### Phase 2: Apply Each Delta

For each delta spec, read both files:

- Delta: `.specs/changes/<name>/specs/<capability>/spec.md`
- Main: `.specs/specs/<capability>/spec.md` (may not exist for new capabilities)

Apply delta markers:

| Delta marker              | Action                                                     |
| ------------------------- | ---------------------------------------------------------- |
| **ADDED** requirements    | Insert as new `### Requirement:` entries in the main spec  |
| **MODIFIED** requirements | Find the matching requirement by name and replace it       |
| **REMOVED** requirements  | Find the matching requirement by name and delete it        |
| **RENAMED** capabilities  | Rename the capability directory and update the spec header |

**Preservation rule:** Content in the main spec not mentioned in the delta is never touched.

**Idempotency rule:** Applying the same delta twice produces the same result as applying it once.
For ADDED: check whether the requirement already exists by name before inserting — skip if already present.
For RENAMED: check whether the new directory name already exists before renaming — skip if already renamed.

**RENAMED processing order:** When a delta spec contains RENAMED alongside other markers, process the rename first (directory rename + spec header update), then apply any ADDED/MODIFIED/REMOVED markers against the already-renamed main spec.
The delta spec is always identified by the _old_ capability name — look it up before renaming.

### Phase 3: Handle New Capabilities

If a delta spec covers a capability with no corresponding main spec:

1. Create `.specs/specs/<capability>/` directory
2. Create `spec.md` in baseline format (no delta markers)
3. Strip the `## ADDED`, `## MODIFIED`, `## REMOVED` section headings and keep the `### Requirement:` entries beneath them as plain requirements

See `references/sdd-spec-formats.md` for the baseline spec format.

If the delta spec contains only RENAMED and the old capability does not exist in main specs, create the capability under the new name using the ADDED requirements as baseline content.

### Phase 4: Update Schema Snapshots (if schemas configured)

If `.sdd/schema-config.yaml` exists and `schemas/after/` is present in the change directory:

1. Copy each schema file from `.specs/changes/<name>/schemas/after/<schema-type>` to `.specs/schemas/<schema-type>` (overwrite).

2. Update `.specs/schemas/.schema-sources.yaml` with the generation date and change name.

3. If the repo contains a committed authored schema (e.g., `docs/openapi.yaml`), surface a reminder — do **not** auto-update it:

   > "Authored schema at `<path>` may need updating to match the implementation.
   > Reference: `.specs/changes/<name>/schemas/after/`"

If no schema config exists, skip silently.

### Phase 5: Validate Output

- [ ] All ADDED requirements appear in the main spec
- [ ] All MODIFIED requirements reflect the updated behavior (old version removed)
- [ ] All REMOVED requirements are gone from the main spec
- [ ] No delta markers (ADDED/MODIFIED/REMOVED/RENAMED) remain in main specs
- [ ] Content not mentioned in deltas is unchanged

### Phase 6: Report

List each capability synced:

```text
Synced:
- auth/          → 2 requirements added, 1 modified
- payments/      → 1 requirement removed
- notifications/ → new capability created (3 requirements)
Schema snapshots updated:
- openapi.yaml   → 2 endpoints added, 1 model modified
- Reminder: authored docs/openapi.yaml may be stale (schema sync did not update it)
```

## Common Mistakes

- Replacing the entire main spec instead of merging selectively
- Leaving delta markers (ADDED/MODIFIED/REMOVED) in the main spec after sync
- Touching content not mentioned in the delta
- Syncing before `sdd-verify` passes

## References

- `references/sdd-spec-formats.md` — baseline spec format for new capabilities created during sync
- `references/sdd-change-formats.md` — change directory artifact formats (proposal, design, tasks)
- `references/sdd-schema.md` — schema lifecycle policy (§ 4) and `.schema-sources.yaml` format (§ 3)
