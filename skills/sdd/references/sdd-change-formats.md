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

## Verification Waivers

- **Requirement:** {requirement name or ID}
  **Reason:** {why automated execution evidence is not feasible — e.g., requires production data, third-party sandbox unavailable, manual operator step}
  **Manual evidence:** {path to captured output, runbook reference, screenshot, or commit where manual verification was recorded}
  **Recorded:** {ISO date or commit SHA when this waiver was first added — used by sdd-verify's provenance check}

## Verification Overrides

- **Finding:** {exact verify finding or stable identifier}
  **Stage:** {workflow stage where the override was applied — usually `verify`, sometimes `sync`}
  **Reason:** {why work must proceed despite the unresolved blocking finding}
  **Constraints:** {what is still forbidden — e.g., no ignore, no suppression, must wait for upstream release}
  **Follow-up task:** {exact unchecked task text or task reference in `tasks.md`}
  **Approved by:** {who explicitly authorized the override — typically `user`}
  **Recorded:** {ISO date or commit SHA when this override was first added}
````

The `## Verification Waivers` section is optional and only present when one or more SHALL requirements cannot be covered by runnable evidence (test, schema check, or captured output).
`sdd-verify` flags any unwaived SHALL without runnable evidence as CRITICAL, and a waiver entry without a checkable manual evidence reference is itself CRITICAL.
The `Recorded` field is required for the provenance check; if absent, `sdd-verify` falls back to `git blame`.

The `## Verification Overrides` section is optional.
User overrides of otherwise blocking findings or gate outcomes are permitted, but they must be recorded in the change artifacts to preserve an audit trail across design, implementation, verify, and sync.
An override does not remove the finding or change its severity; it only records that work proceeded despite the blocker.
Each override must identify what was overridden, where in the workflow the intervention happened, why work continued, what remained forbidden, who approved it, and what follow-up work stayed open.

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
- If a blocking verify finding or gate outcome is explicitly overridden, keep or add an unchecked remediation task in `tasks.md` that names the fix still required.
- Every SHALL requirement in the delta specs must be backed by at least one task that produces runnable evidence — a named test (unit, integration, or e2e), a schema-snapshot check, or a captured-output step.
  Requirements that genuinely cannot be tested automatically belong in `design.md` § Verification Waivers instead.
  `sdd-verify` enforces this rule and will flag uncovered SHALL requirements as CRITICAL.
