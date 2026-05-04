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

## Invocation Notice

- Inform the user when this skill is being invoked by name: `sdd-apply`.

## Hard Gate

**If `tasks.md` does not exist for the active change: STOP.**

> "No tasks to implement. Run `sdd-propose` first to create the change artifacts."

Do not proceed without tasks.md.

## Critical Constraints

**Never reference ephemeral scaffolding in any persisted artifact.**

Ephemeral scaffolding includes:

- Task IDs and task numbers (e.g. `Task 7.4`, `T12`)
- Group names and group numbers (e.g. `Group 8`, `G3`)
- Design-section IDs (e.g. `D12`, `design §4.2`)
- Other planning-artifact identifiers that won't outlive the change

These must not appear in:

- Code, symbols, or filenames
- Comments or docstrings
- Commit messages (subject, body, or footer)
- PR titles or descriptions
- Any other artifact that persists after the change is archived

Tasks, groups, and design-section IDs are scaffolding for the current change.
Once archived, only the spec name persists — references to ephemeral IDs become meaningless noise to future readers.
Name things after _what they do_, not where they came from in `tasks.md` or `design.md`.
If you catch yourself writing "D12 wiring" or "Task 7.4 implementation," restate it in terms of the behavior or component being changed.

**This applies whether or not the `commit-message` skill is available.**
When drafting a commit message during apply:

- Prefer invoking `commit-message` if it is loadable in this environment.
- Otherwise, draft a Conventional Commit (`type(scope): subject`) that describes _what changed and why_, and apply the constraints above.
- Do not paste design or task identifiers into the message even if they appear in the surrounding tasks/design files.

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
6. If `.specs/.sdd/schema-config.yaml` exists, identify tasks that define schema contracts (endpoint definitions, model schemas, DDL changes) and check that they are sequenced before any tasks that consume them in `tasks.md`.
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
4. **Check for newly-emerged write-sites** — see § Write-site emergence below
5. **Test** — verify the implementation works
   If the test fails, stop and resolve the failure before proceeding to the next step.
6. **Check off** — update `tasks.md`: `- [ ]` → `- [x]`

Follow design decisions in `design.md` — don't diverge without reason.
Follow behavioral requirements in delta specs — these define what "correct" means.
Apply the **Critical Constraints** above to every artifact you produce — code, comments, and commit messages alike.

If `.specs/.sdd/schema-config.yaml` exists and a task consumes a schema contract that is not yet defined, pause before implementing it.
Surface the dependency gap and confirm with the user whether to reorder tasks in `tasks.md` first.

### Write-site emergence

A SHALL requirement may end up with multiple code paths that produce or modify the contract-asserted value during implementation — not just the canonical path.
Common examples: deduplication shortcuts, cache fast-paths, retry/fallback branches, idempotency early-returns, merge or composition steps that write the same fields.

When implementing a task introduces such a path for an existing SHALL:

1. **Pause before checking off** the implementation task.
2. **Add a paired test task** to `tasks.md` that exercises the contract _through the new path_.
   The new test task must produce runnable evidence (test, schema check, or captured output) — same standard as the original SHALL coverage rule.
3. **Implement the test** as part of the same work, or sequence it as the immediately-following task.
4. **Then** check off the original implementation task.

A test exercising only the canonical path does not stand in for evidence on a shortcut, retry, or composition path.
This rule is what `sdd-verify`'s write-site enumeration is checking; cover it at apply time and verify has nothing to flag.

When unsure whether a path is contract-relevant, surface it to the user rather than skipping the test task silently.

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
- Adding a deduplication shortcut, cache fast-path, retry branch, or composition step for a SHALL-covered value without adding a paired test task that exercises the new write-site (see § Write-site emergence)
- Checking off the implementation task before the paired test task for a newly-emerged write-site is added and runnable
- Referencing ephemeral scaffolding — task IDs, group names, design-section IDs (e.g. `D12`) — in code, comments, commit messages, or PR descriptions (see **Critical Constraints**)
- Drafting a commit message inline without invoking `commit-message` when it is available, or without applying the **Critical Constraints** when it is not

## References

- `references/sdd-schema.md` — schema config format (§ 3) and lifecycle policy (§ 4)
