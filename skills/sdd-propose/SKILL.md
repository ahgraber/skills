---
name: sdd-propose
description: |-
  Use when creating a new change with all SDD artifacts — proposal, delta specs, design, and tasks. Triggers: "propose a change", "create a change for X", "I want to implement feature Y", "start a new change", "let's build X".
---

# SDD Propose

Create a change directory with all SDD artifacts.
Generates artifacts in dependency order: proposal → delta specs → design → tasks.

## When to Use

- Starting a new feature or behavioral change
- User knows what they want to build and is ready to create a full change
- No active change exists for this work

## When Not to Use

- Existing specs to convert from another tool — use `sdd-translate`
- Deriving specs from code analysis — use `sdd-derive`
- A change already exists and needs implementation — use `sdd-apply`
- Need to think before speccing — use `sdd-explore` first

## Process

### Phase 1: Understand the Change

Ask the user:

1. **What are we building?** — feature, bugfix, refactor, migration?
2. **Change name** — kebab-case identifier (e.g., `user-auth-refresh`, `payment-retry`)
3. **Which capabilities does it touch?** — which existing specs are affected?

Read `.specs/specs/` to understand existing baseline specs before generating deltas.
If `.specs/specs/` is empty or does not exist, generate delta specs using only ADDED sections — all behavior is new.

If the user isn't sure about scope, offer `sdd-explore` first.

### Phase 2: Generate proposal.md

Create `.specs/changes/<name>/proposal.md`.

See `references/sdd-formats.md` for the complete proposal format.

Write with the user's input:

- Intent: the why — problem being solved
- Scope: concrete in/out lists
- Approach: high-level direction
- Open Questions: unresolved decisions (if any)

Present to user and confirm before continuing.

### Phase 3: Generate Delta Specs

Create `.specs/changes/<name>/specs/<capability>/spec.md` for each affected capability.

See `references/sdd-formats.md` for the complete delta spec format.

Rules:

- Read the existing baseline spec before writing the delta
- Only include capabilities that actually change
- Use only ADDED/MODIFIED/REMOVED/RENAMED sections that apply — omit empty sections
- MODIFIED: state new and previous behavior inline

Present specs to user and confirm before continuing.

### Phase 4: Generate design.md

Create `.specs/changes/<name>/design.md`.

See `references/sdd-formats.md` for the complete design format.

Include:

- Context: architectural constraints or existing decisions that affect this change
- Decisions: each non-obvious choice with rationale and alternatives considered
- Architecture: ASCII diagrams of component relationships, data flows
- Risks: what could go wrong and mitigation

Only include sections with content — omit empty sections.

Present to user and confirm before continuing.

### Phase 5: Generate tasks.md

Create `.specs/changes/<name>/tasks.md`.

See `references/sdd-formats.md` for the complete tasks format.

Rules:

- Tasks are atomic — each can be done and tested independently
- Order by implementation dependency (what must be done first)
- Group by component or phase
- Every task is a concrete action, not an outcome

### Phase 6: Validate

- [ ] Change directory exists: `.specs/changes/<name>/`
- [ ] `proposal.md` has Intent, Scope (in/out), Approach
- [ ] Delta specs use only ADDED/MODIFIED/REMOVED/RENAMED sections (no baseline format)
- [ ] `design.md` has at least one Decision with rationale
- [ ] `tasks.md` has atomic, ordered tasks
- [ ] No delta markers in `.specs/specs/` (baseline specs untouched)

## Output

- `.specs/changes/<name>/proposal.md`
- `.specs/changes/<name>/specs/<capability>/spec.md` per affected capability (delta format)
- `.specs/changes/<name>/design.md`
- `.specs/changes/<name>/tasks.md`

Summary: change name, capabilities affected, task count.

## Common Mistakes

- Not reading existing baseline specs before writing deltas
- Writing baseline format in change specs (missing ADDED/MODIFIED/REMOVED markers)
- Creating tasks that are too coarse (one task = "implement auth" instead of atomic steps)
- Generating all artifacts without pausing for user confirmation between phases
- Using non-kebab-case change names

## References

- `references/sdd-formats.md` — complete format reference for all artifact types
