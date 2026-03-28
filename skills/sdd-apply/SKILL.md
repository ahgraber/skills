---
name: sdd-apply
description: |-
  Use when implementing tasks from a change's tasks.md. Triggers: "apply tasks", "implement the change", "work through tasks", "start implementing", "continue implementing", "apply the change".
---

# SDD Apply

Implement tasks from `SPECS_ROOT/changes/<name>/tasks.md`.
Check off each task as it completes.

> `SPECS_ROOT` is resolved by the `sdd` router before this skill runs.
> Replace `.specs/` with your project's actual specs root in all paths below.

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
6. If `.sdd/schema-config.yaml` exists, identify tasks that define schema contracts (endpoint definitions, model schemas, DDL changes) and check that they are sequenced before any tasks that consume them in `tasks.md`.
   Surface any ordering gaps to the user before implementing.

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

Follow design decisions in `design.md` — don't diverge without reason.
Follow behavioral requirements in delta specs — these define what "correct" means.

If `.sdd/schema-config.yaml` exists and a task consumes a schema contract that is not yet defined, pause before implementing it.
Surface the dependency gap and confirm with the user whether to reorder tasks in `tasks.md` first.

### Phase 4: After All Tasks

When all tasks are checked off:

> "All tasks complete. Recommended next steps:
>
> 1. Run `sdd-verify` to confirm implementation matches the change artifacts
> 2. Run `sdd-sync` to merge delta specs into main specs
> 3. Run `sdd-archive` to complete the change"

## Fluid Workflow

This skill can be invoked at any point after `tasks.md` exists — not only when all artifacts are complete.

- If implementation reveals a design issue, pause and suggest updating `design.md` or delta specs before continuing.
- If scope changes mid-implementation, suggest updating `proposal.md` and `tasks.md`.
- Don't treat the artifact set as frozen — work fluidly, but document changes.

## Common Mistakes

- Implementing without reading design.md (misses architectural decisions)
- Not checking off tasks as they complete
- Implementing tasks out of order when dependencies exist
- Continuing past a failed task without resolving it
- Diverging from design decisions without documenting why
- Treating artifacts as frozen when implementation reveals issues (update them)

## References

- `references/sdd-schema.md` — schema config format (§ 3) and lifecycle policy (§ 4)
