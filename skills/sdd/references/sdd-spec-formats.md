---
name: sdd-spec-formats
description: SDD spec artifact formats — RFC 2119 keywords, baseline spec, delta spec, and scenario format. Referenced by sdd-translate, sdd-derive, sdd-propose, and sdd-sync.
---

# SDD Spec Formats

Format reference for `.specs/` artifact files.

## 1. RFC 2119 Keywords

| Keyword      | Meaning                                        |
| ------------ | ---------------------------------------------- |
| SHALL / MUST | Mandatory — no exceptions                      |
| SHOULD       | Recommended — exceptions require justification |
| MAY          | Optional — permitted but not required          |

- Use **SHALL** for non-negotiable system behaviors
- Use **MUST** for non-negotiable user/actor obligations
- Use **SHOULD** for strong recommendations
- Use **MAY** for optional behaviors

## 2. Baseline Spec Format

Location: `.specs/specs/<capability>/spec.md`

```markdown
# {Capability} Specification

> {Optional: translation note, generation note, or source attribution}
> {e.g., "Translated from Spec Kit on 2026-01-15" or "Generated from code analysis on 2026-01-15"}

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

- **Implementation**: {source files or leave blank}
- **Dependencies**: {related capabilities or "none"}
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

## 4. Scenario Format

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
