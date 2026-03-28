---
name: sdd-translate
description: |-
  Use when translating or migrating existing specs from another tool or format (Spec Kit, Kiro, ADRs, Jira, Confluence, Word docs, or custom markdown requirements) into SDD baseline spec format. Also use when the user says "convert these specs", "migrate to SDD", "translate from X to SDD", or "import specs".
---

# SDD Translate

Convert existing specifications from other frameworks, tools, or formats into SDD baseline `spec.md` files in `SPECS_ROOT/specs/<capability>/`.

> `SPECS_ROOT` is resolved by the `sdd` router before this skill runs.
> Replace `.specs/` with your project's actual specs root in all paths below.

## When to Use

- Migrating from Spec Kit, Kiro, ADRs, Jira, Confluence, or similar
- Converting structured requirements documents into SDD format
- Reverse-engineering third-party spec output into `.specs/specs/`

## When Not to Use

- No existing specs to translate — use `sdd-derive` instead
- Already in SDD format — run `sdd-verify` to check completeness

## Process

### Phase 1: Inventory Source Specs

1. **Identify source format and structure:**

   - Spec Kit → `spec.md` + `plan.md` with Markdown headings
   - Kiro → steering docs + requirements files
   - ADRs → architecture decision records (context/decision/consequences)
   - Jira/Linear → issue descriptions + acceptance criteria
   - Prose documents → natural language requirements

2. **Read all source files** before generating anything.

3. **Group into capabilities** — logical groupings that will each become one `.specs/specs/<capability>/spec.md`:

   - By feature area: `auth/`, `payments/`, `notifications/`
   - By component: `api/`, `frontend/`, `workers/`
   - By bounded context: `ordering/`, `fulfillment/`

### Phase 2: Assess Scope and Plan Decomposition

Before generating specs, count requirements across all source material:

| Signal                 | Action                                                  |
| ---------------------- | ------------------------------------------------------- |
| ≤ 8 requirements total | Single capability, proceed directly                     |
| 9–20 requirements      | Split into 2–4 capabilities, proceed                    |
| 20+ requirements       | Present capability split to user, wait for confirmation |

When decomposing, present the proposed split:

```text
Proposed capabilities:
- auth/      → login, session, token management (5 reqs)
- payments/  → billing, subscriptions (6 reqs)
- ui/        → themes, layout (4 reqs)

Proceed with this split? (or suggest changes)
```

### Phase 3: Translate Each Capability

For each capability, produce `.specs/specs/<capability>/spec.md` following SDD baseline format.

See `references/sdd-spec-formats.md` for the baseline spec and scenario formats.

Add a source attribution blockquote at the top of each generated spec (see format reference Section 2):

> Translated from {source tool/format} on {date}
> Source: {source file or description}

**Translation rules:**

| Source pattern                                 | SDD translation                                                       |
| ---------------------------------------------- | --------------------------------------------------------------------- |
| "Users can X"                                  | `The system SHALL allow users to X`                                   |
| Acceptance criteria bullets                    | `#### Scenario:` entries with GIVEN/WHEN/THEN                         |
| "It should Y"                                  | `The system SHOULD Y`                                                 |
| "Required: Z"                                  | `The system MUST Z`                                                   |
| Implementation detail (class names, libraries) | Move to `## Technical Notes` or omit                                  |
| Phase-gated steps (plan.md, tasks.md)          | Omit — not behavior                                                   |
| "As a user, I want X so that Y"                | `The system SHALL allow users to X` (discard the "so that" rationale) |
| "Shall not / Must not"                         | `The system SHALL NOT / MUST NOT {prohibited behavior}`               |
| Numbered requirement IDs (e.g., `REQ-001:`)    | Strip the ID prefix; preserve the requirement text                    |

**Critical rules:**

- Requirements describe WHAT, not HOW
- Every scenario must have **GIVEN**, **WHEN**, **THEN** (bold labels, exact casing)
- Scenarios use `####` (4 hashtags), requirements use `###` (3 hashtags)
- No delta markers (ADDED/MODIFIED/REMOVED) — these are baseline specs

### Phase 4: Validate Output

- [ ] Every `### Requirement:` uses RFC 2119 keywords (SHALL/MUST/SHOULD/MAY)
- [ ] Every scenario uses **GIVEN**/**WHEN**/**THEN** with bold labels
- [ ] No implementation details in requirements (class names, SQL, library choices)
- [ ] `## Purpose` section present in each spec
- [ ] Scenarios use `####` heading level (not `###` or `#####`)
- [ ] No delta markers (ADDED/MODIFIED/REMOVED)
- [ ] No implementation details copied into requirement text (class names, SQL, library choices, technology decisions)
- [ ] Implementation details from source were moved to `## Technical Notes` where present

### Phase 5: Schema Snapshot (if schemas configured)

If `.sdd/schema-config.yaml` exists:

1. Generate schema snapshots using the configured extraction commands.
2. Store in `.specs/schemas/` — this establishes the baseline for all future `sdd-verify` conformance checks.
3. Update `.specs/schemas/.schema-sources.yaml` with the generation date.

If no schema config exists but schema artifacts are detected in the repo (e.g., `openapi.yaml`, `.proto` files, `schema.graphql`), suggest creating `.sdd/schema-config.yaml` before the first `sdd-verify` run:

> "Detected schema artifacts. A `.sdd/schema-config.yaml` would let `sdd-verify` cross-validate implementation against these specs. See `references/sdd-schema.md` § 3 for the format. Say 'skip' to dismiss."

If no schema config and no artifacts detected, skip silently.

## Output

- `.specs/specs/<capability>/spec.md` per capability
- Summary: capabilities created, requirement count per capability, translation notes and assumptions

## Common Mistakes

- Copying implementation detail from source files into requirements
- Using non-RFC-2119 language ("the system will", "users can") instead of SHALL/MUST/SHOULD
- One giant spec instead of capability decomposition for large surface areas
- Including delta markers (ADDED/MODIFIED) in baseline specs
- Not reading all source files before generating output

## References

- `references/sdd-spec-formats.md` — baseline spec and scenario formats
- `references/sdd-schema.md` — schema config format and lifecycle policy
