---
name: sdd-formats
description: SDD artifact format reference — baseline specs, delta specs, proposals, designs, tasks, RFC 2119 keywords, and scenarios. Referenced by sdd-translate, sdd-derive, sdd-propose, and sdd-sync.
---

# SDD Format Reference

Shared format reference for all SDD skill artifacts.
All skills that produce `.specs/` files SHALL conform to these formats.

## 1. RFC 2119 Keywords

| Keyword      | Meaning                                        |
| ------------ | ---------------------------------------------- |
| SHALL / MUST | Mandatory — no exceptions                      |
| SHOULD       | Recommended — exceptions require justification |
| MAY          | Optional — permitted but not required          |

- Use SHALL for non-negotiable system behaviors
- Use MUST for non-negotiable user/actor obligations
- Use SHOULD for strong recommendations
- Use MAY for optional behaviors

## 2. Baseline Spec Format

Location: `.specs/specs/<capability>/spec.md`

```markdown
# {Capability} Specification

> Translated from {Source} on {date}.

## Purpose

{2-3 sentence description of what this capability does and why it exists.}

## Requirements

### Requirement: {RequirementName}

The system SHALL/MUST/SHOULD/MAY {observable behavior}.

#### Scenario: {ScenarioName}

- **GIVEN** {precondition}
- **WHEN** {action}
- **THEN** {expected outcome}

## Technical Notes

- **Implementation:** {relevant implementation notes}
- **Dependencies:** {external dependencies or related capabilities}
```

Rules:

- No delta markers (ADDED/MODIFIED/REMOVED/RENAMED) in baseline specs
- Each requirement uses a single RFC 2119 keyword
- Scenarios use `####` heading level exactly
- Scenario labels (GIVEN/WHEN/THEN) are bold: `**GIVEN**`, `**WHEN**`, `**THEN**`
- `## Technical Notes` is optional but recommended

## 3. Delta Spec Format

Location: `.specs/changes/<name>/specs/<capability>/spec.md`

```markdown
# Delta for {Capability}

## ADDED Requirements

### Requirement: {RequirementName}

The system SHALL/MUST/SHOULD/MAY {new observable behavior}.

#### Scenario: {ScenarioName}

- **GIVEN** {precondition}
- **WHEN** {action}
- **THEN** {expected outcome}

## MODIFIED Requirements

### Requirement: {RequirementName}

The system SHALL/MUST/SHOULD/MAY {new behavior}. (Previously: {old behavior summary})

## REMOVED Requirements

### Requirement: {RequirementName}

Removed because: {reason for removal}.

## RENAMED Capabilities

{OldName} → {NewName}

Reason: {why the capability was renamed}.
```

Rules:

- Only include sections that apply — omit empty ADDED/MODIFIED/REMOVED/RENAMED sections
- MODIFIED must state both new and previous behavior inline
- REMOVED entries must include a reason
- No `## Purpose` or `## Technical Notes` in delta specs

## 4. Proposal Format

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

## 5. Design Format

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

```text
{ASCII diagram illustrating the system structure or data flow}
```

## Risks

- {risk}: {mitigation strategy}
````

## 6. Tasks Format

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
- Tasks describe implementation actions, not outcomes
- Groups organize by component or phase
- Use `- [x]` to mark completed tasks

## 7. Scenario Format

Used in both baseline and delta spec requirements.

```markdown
#### Scenario: {ScenarioName}

- **GIVEN** {precondition — the starting state}
- **WHEN** {action — the trigger}
- **THEN** {expected outcome — the observable result}
```

Rules:

- Each scenario MUST have all three labels: GIVEN, WHEN, THEN
- Labels are bold with no colon: `**GIVEN**`, `**WHEN**`, `**THEN**`
- One scenario per observable behavior path
- Scenarios describe external behavior, never implementation details
