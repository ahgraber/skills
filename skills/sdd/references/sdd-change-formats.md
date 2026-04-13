---
name: sdd-change-formats
description: SDD change artifact formats — proposal, design, and tasks. Referenced by sdd-propose and sdd-derive.
---

# SDD Change Formats

Format reference for change directory artifacts.

## 1. Proposal Format

Location: `.specs/changes/<name>/proposal.md`

```markdown
# Proposal: {Change Name}

## Intent

{2-4 sentences describing why this change is needed and what problem it solves.}

## Scope

**In scope:**

- {item}

**Out of scope:**

- {item}

## Approach

{High-level technical direction and strategy for implementing this change.}

## Open Questions

- {Unresolved decision or question that must be answered before implementation}
```

Rules:

- Intent is the "why" — not the "what" or "how"
- Scope prevents scope creep — be explicit about boundaries
- Open Questions is optional — omit if there are none
- **Approach** is the draft sandbox for mechanism thinking during spec authoring.
  Early algorithm, heuristic, or strategy ideas that surface while writing the contract belong here until they are formalized into `design.md`.
  This keeps mechanism out of `spec.md` without losing the thinking.

## 2. Design Format

`design.md` is the **legitimate home for mechanism** — chosen algorithms, heuristics, thresholds, data structures, strategies, retry policies, model choices, similarity metrics, and architectural decisions.
If a draft spec sentence names one of these, it probably belongs here rather than in `spec.md`.
See `sdd-spec-formats.md` § 1.3 for the spec/design/tasks responsibility split.

Location: `.specs/changes/<name>/design.md`

````markdown
# Design: {Change Name}

## Context

{Background, constraints, and assumptions that shape this design.}

## Decisions

### Decision: {DecisionName}

**Chosen:** {the selected approach}

**Rationale:** {why this approach was chosen}

**Alternatives considered:**

- {alternative}: {why it was not chosen}

## Architecture

{ASCII diagram or prose description of component relationships and data flows.}

```text
{optional ASCII art}
```

## Risks

- **{Risk}**: {mitigation strategy}
````

## 3. Tasks Format

Location: `.specs/changes/<name>/tasks.md`

```markdown
# Tasks: {Change Name}

## {Group Name}

- [ ] {Concrete, atomic implementation step}
- [ ] {Concrete, atomic implementation step}

## {Another Group Name}

- [ ] {Concrete, atomic implementation step}
- [x] {Completed implementation step}
```

Rules:

- Tasks are atomic — each task is a single, completable unit of work
- Tasks describe implementation actions, not outcomes (the outcomes live in `spec.md`)
- Groups organize by component or phase (e.g., 'Backend', 'Frontend', 'Tests')
- Use `- [x]` to mark completed tasks
