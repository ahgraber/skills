---
name: sdd
description: |-
  Use when the user wants to do any spec-driven development work — creating, deriving, or inheriting specs, managing changes, implementing from specs, or verifying implementations. Triggers: 'spec this out', 'create a spec', 'implement from spec', 'apply tasks', 'verify implementation', 'sync specs', 'archive change', 'sdd', any mention of .specs/ directory or spec-driven workflow.
---

# SDD — Spec Driven Development

Route user intent to the correct `sdd-*` child skill.
Classify first, then confirm with the user before routing.

## Invocation Notice

When this skill is invoked, announce: "Using **sdd** to route your spec-driven development request."

## Trigger Tests

Should trigger:

- "Spec this feature out"
- "I want to create a change proposal"
- "Apply the tasks in my change"
- "Verify that I implemented everything correctly"
- "Sync the delta specs into main"
- "Archive the auth-refactor change"
- "I want to think through this before speccing it"

Should not trigger:

- "Write a commit message"
- "Debug this Python error"
- "Review my PR"

## Locate Specs Root

Before routing, resolve the specs root for this session:

1. Use `Glob` with pattern `**/.specs/**` to find files inside any `.specs/` directory, then extract the unique `.specs/` parent paths from results. (Glob matches files only — searching for files _inside_ `.specs/` is how you locate the directories.)
2. **Multiple found** — list them and ask the user which to use.
3. **Exactly one found** — use it; announce the resolved path.
4. **None found** — ask the user where to initialize `.specs/` (default: repo root).
5. **User specifies a path explicitly** — use that path regardless of search results.

> **Escape hatch:** If discovery requires more complex logic (empty directories, unusual nesting, or large monorepos), add a helper script at `skills/sdd/scripts/find-specs-roots.sh` and reference it here. Until then, fall back to `find . -type d -name ".specs" -maxdepth 4` via Bash if Glob returns no results.

Call the resolved path `SPECS_ROOT`.
All child skills use `SPECS_ROOT` in place of `.specs/`.

## Route by Intent

| User Intent                              | Route           | Notes                  |
| ---------------------------------------- | --------------- | ---------------------- |
| Think before acting, explore ideas       | `sdd-explore`   | Always available       |
| Convert existing specs from another tool | `sdd-translate` | Bootstrap path         |
| Generate specs from codebase analysis    | `sdd-derive`    | Bootstrap or change    |
| Create a change with all artifacts       | `sdd-propose`   | Change path            |
| Implement tasks from tasks.md            | `sdd-apply`     | Requires tasks.md      |
| Verify implementation matches specs      | `sdd-verify`    | Requires active change |
| Merge delta specs into main specs        | `sdd-sync`      | Requires delta specs   |
| Complete and archive a change            | `sdd-archive`   | Requires active change |

## Routing Flowchart

```dot
digraph sdd_router {
    rankdir=TB;
    node [fontname="Helvetica", fontsize=10];
    edge [fontname="Helvetica", fontsize=9];

    start [label="User intent", shape=ellipse];
    locate_root [label="Locate SPECS_ROOT\n(.specs/ directories)", shape=box];
    multi_specs [label="Multiple .specs/\nfound?", shape=diamond];
    ask_which [label="Ask user which\nto use", shape=box];

    explore_first [label="Wants to think\nbefore acting?", shape=diamond];
    explore [label="sdd-explore", shape=box];

    has_specs [label="SPECS_ROOT/specs/ exists?", shape=diamond];
    confirm_mode [label="Confirm intent\nwith user", shape=box];

    translate [label="sdd-translate", shape=box];
    derive [label="sdd-derive", shape=box];
    propose [label="sdd-propose", shape=box];

    has_change [label="Active change exists?", shape=diamond];
    which_change [label="Which change?\n(ask if multiple)", shape=box];
    has_tasks [label="tasks.md exists?", shape=diamond];
    stop [label="STOP:\nrun sdd-propose first", shape=octagon, style=filled, fillcolor=red, fontcolor=white];
    apply [label="sdd-apply", shape=box];
    verify [label="sdd-verify", shape=box];
    sync [label="sdd-sync", shape=box];
    archive [label="sdd-archive", shape=box];

    start -> locate_root;
    locate_root -> multi_specs;
    multi_specs -> ask_which [label="yes"];
    multi_specs -> explore_first [label="no (0 or 1)"];
    ask_which -> explore_first;

    explore_first -> explore [label="yes"];
    explore_first -> has_specs [label="no, ready to act"];

    explore -> has_specs [label="crystallized,\nready to act", style=dashed];

    has_specs -> confirm_mode;
    confirm_mode -> translate [label="convert existing specs"];
    confirm_mode -> derive [label="spec from code"];
    confirm_mode -> propose [label="new change"];
    confirm_mode -> has_change [label="apply/verify/\nsync/archive"];
    confirm_mode -> explore [label="think more"];

    has_change -> which_change [label="yes"];
    has_change -> propose [label="no", style=dashed];

    which_change -> has_tasks [label="apply"];
    which_change -> verify [label="verify"];
    which_change -> sync [label="sync"];
    which_change -> archive [label="archive"];

    has_tasks -> apply [label="yes"];
    has_tasks -> stop [label="no"];
}
```

## Routing Rules

1. **Resolve SPECS_ROOT first** — locate `.specs/` before routing; ask if multiple exist or user specifies a path
2. **Classify intent** — explore-or-act, then determine path
3. **Infer mode from directory state** — check `SPECS_ROOT/specs/` existence — but **always confirm with user** before routing
4. **One hard gate** — `sdd-apply` requires `tasks.md` at `SPECS_ROOT/changes/<change-name>/tasks.md`; if missing, stop and route to `sdd-propose`
5. **Prefer minimal next step** — don't run the full pipeline unless requested
6. **Explore is mode-agnostic** — available at every stage, before or after any action
7. **Multiple active changes** — ask which change before routing to apply/verify/sync/archive

## Sequence Gates

| Action      | Expected prerequisite                | Warning if missing                                               |
| ----------- | ------------------------------------ | ---------------------------------------------------------------- |
| sdd-apply   | `SPECS_ROOT/changes/<name>/tasks.md` | **Hard block** — "No tasks to implement. Run sdd-propose first." |
| sdd-verify  | Some completed tasks in `tasks.md`   | "No completed tasks yet — verify output will be limited."        |
| sdd-sync    | Delta specs in change directory      | "No delta specs to sync."                                        |
| sdd-archive | All tasks complete                   | "Incomplete tasks remain. Archive anyway?" (ask user)            |
| design.md   | `proposal.md` exists                 | "Consider writing a proposal first for context."                 |

## Directory Convention

All SDD skills operate on `SPECS_ROOT` — resolved at session start (see **Locate Specs Root** above).
The default is `.specs/` at the project root, but monorepos or user preference may place it elsewhere (e.g., `packages/api/.specs/`, `services/auth/.specs/`).

Child skills replace `.specs/` with `SPECS_ROOT` in all paths.

```text
<SPECS_ROOT>/          # e.g. .specs/ or packages/api/.specs/
├── specs/                          # Main specs (source of truth)
│   └── <capability>/
│       └── spec.md
├── schemas/                        # Schema snapshots (generated from code)
│   ├── .schema-sources.yaml        # Manifest: generation date and source per schema
│   └── <schema-type>               # e.g., openapi.yaml, db-schema.sql, schema.graphql
├── changes/
│   ├── <change-name>/              # In-progress changes (kebab-case)
│   │   ├── proposal.md
│   │   ├── design.md
│   │   ├── tasks.md
│   │   ├── schemas/                # Schema snapshots scoped to this change
│   │   │   ├── before/             # Snapshot taken at propose/derive time
│   │   │   ├── after/              # Snapshot taken at verify time
│   │   │   └── expected.md         # Prose: expected schema changes
│   │   └── specs/                  # Delta specs
│   │       └── <capability>/
│   │           └── spec.md
│   └── archive/                    # Completed changes (schemas travel with change)
│       └── YYYY-MM-DD-<name>/
├── .sdd/                           # SDD tooling metadata
│   ├── schema-config.yaml          # Project schema extraction config
│   └── suggested-tools             # Tracks one-time tool suggestions
```

An **active change** is any directory directly under `SPECS_ROOT/changes/` (not under `archive/`).
Archived changes live in `SPECS_ROOT/changes/archive/YYYY-MM-DD-<name>/`.
Schema snapshots travel with the change directory into the archive — no separate schema archive path is needed.

## References

- `references/sdd-spec-formats.md` — baseline spec, delta spec, scenario formats
- `references/sdd-change-formats.md` — proposal, design, tasks formats
- `references/sdd-schema.md` — schema artifacts and lifecycle policy
- `references/sdd-router.dot` — canonical DOT source for the routing flowchart above
