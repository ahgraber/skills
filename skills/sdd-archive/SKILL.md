---
name: sdd-archive
description: |-
  Use when completing and archiving a change after all tasks are done and specs are synced. Triggers: "archive the change", "complete this change", "close out the change", "finish the change", "archive".
---

# SDD Archive

Complete a change by moving its directory to the archive.

> `SPECS_ROOT` is resolved by the `sdd` router before this skill runs.
> Replace `.specs/` with your project's actual specs root in all paths below.

## When to Use

- All tasks in `tasks.md` are complete (`- [x]`)
- Delta specs have been synced into main specs with `sdd-sync`
- Ready to close out the change

## When Not to Use

- Tasks are incomplete — finish implementation first
- Delta specs exist but haven't been synced — consider running `sdd-sync` first (no automatic check; user judgement)

## Soft Gate

Check `tasks.md` for unchecked tasks before archiving.

If incomplete tasks remain:

> "{N} tasks are still incomplete. Archive anyway?"

Wait for user confirmation before proceeding.

## Process

### Phase 1: Confirm

1. Confirm which change to archive (ask if multiple active changes exist)
2. Read `tasks.md` — count complete vs. total tasks
3. If incomplete tasks: issue soft gate warning, wait for user

### Phase 2: Check Target

Target path: `.specs/changes/archive/YYYY-MM-DD-<change-name>/`

Where `YYYY-MM-DD` is today's date.

If the target already exists:

> "Archive target already exists: `.specs/changes/archive/{date}-{name}/`. Suggest using `{name}-2` or waiting until tomorrow."

Stop and ask the user how to proceed.

### Phase 3: Move

```bash
mkdir -p .specs/changes/archive/
mv .specs/changes/<name>/ .specs/changes/archive/YYYY-MM-DD-<name>/
```

Confirm the move succeeded by checking the archive path exists.

### Phase 4: Report

```text
Archived: .specs/changes/<name>/ → .specs/changes/archive/YYYY-MM-DD-<name>/
Tasks: {N}/{N} complete
```

## Common Mistakes

- Deleting instead of moving (archive, not delete — change history is preserved)
- Archiving before syncing delta specs into main specs
- Not checking for the target path existence before moving
