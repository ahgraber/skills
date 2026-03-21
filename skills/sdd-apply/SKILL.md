---
name: sdd-apply
description: |-
  Use when implementing tasks from a change's tasks.md. Checks off tasks as completed. Hard gate: tasks.md must exist or execution stops. Triggers: "apply tasks", "implement the change", "work through tasks", "start implementing", "continue implementing", "apply the change".
---

# SDD Apply

Implement tasks from `.specs/changes/<name>/tasks.md`.
Check off each task as it completes.

## Hard Gate

**If `tasks.md` does not exist for the active change: STOP.**

> "No tasks to implement. Run `sdd-propose` first to create the change artifacts."

Do not proceed without tasks.md.

## When to Use

- A change has `tasks.md` and implementation should begin or continue
- Resuming implementation after a pause

## When Not to Use

- No `tasks.md` exists — run `sdd-propose` first
- All tasks complete — run `sdd-verify`, then `sdd-sync`, then `sdd-archive`

## Process

### Phase 1: Load Context

1. Confirm which change to apply (ask if multiple active changes exist)
2. Read `.specs/changes/<name>/tasks.md` — full task list
3. Read `.specs/changes/<name>/design.md` — architectural decisions to follow
4. Read `.specs/changes/<name>/specs/` — delta specs for behavioral requirements
5. Read `.specs/specs/` — baseline specs for full context

### Phase 2: Identify Starting Point

Check tasks.md for already-completed tasks (`- [x]`).
Start from the first unchecked task.

If all tasks are complete:

> "All tasks are already complete. Run `sdd-verify` to confirm the implementation, then `sdd-sync` and `sdd-archive`."

Stop.

### Phase 3: Implement Task-by-Task

For each unchecked task:

1. **Read the task** — understand what it requires
2. **Check dependencies** — are earlier tasks complete?
   If not, implement them first
3. **Implement** — write the code
4. **Test** — verify the implementation works
   If the test fails, stop and resolve the failure before proceeding to the next step.
5. **Check off** — update `tasks.md`: `- [ ]` → `- [x]`
6. **Commit** — include both the implementation code and the updated `tasks.md` check-off in the same commit

Follow design decisions in `design.md` — don't diverge without reason.
Follow behavioral requirements in delta specs — these define what "correct" means.

### Phase 4: After All Tasks

When all tasks are checked off:

> "All tasks complete. Recommended next steps:
>
> 1. Run `sdd-verify` to confirm implementation matches the change artifacts
> 2. Run `sdd-sync` to merge delta specs into main specs
> 3. Run `sdd-archive` to complete the change"

## Common Mistakes

- Implementing without reading design.md (misses architectural decisions)
- Not checking off tasks as they complete
- Implementing tasks out of order when dependencies exist
- Continuing past a failed task without resolving it
- Diverging from design decisions without documenting why
