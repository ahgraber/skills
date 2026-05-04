---
name: sdd-spec-formats
description: SDD spec artifact formats — what a requirement is (contract shapes), RFC 2119 keywords, baseline spec, delta spec, and scenario format. Referenced by sdd-translate, sdd-derive, sdd-propose, sdd-verify, and sdd-sync.
---

# SDD Spec Formats

Format reference for `.specs/` artifact files.
Start with § 1 before writing any requirement — it defines what a requirement _is_.
The later sections define how requirements are packaged into files.

## 1. What a Requirement Is

A requirement is a **contract statement** — a claim about observable state that must hold.
It is not a narration of what the system does, nor a description of how it does it.
Mechanism, strategy, and steps belong in other artifacts (see § 1.3).

### 1.1 Contract shapes

Every requirement takes one of these shapes.
If a draft doesn't fit any shape, it is probably describing procedure or architecture; relocate it to `design.md` or `tasks.md`.

- **Guarantee** — something observable that SHALL be true after an event.
  _Example:_ "The user SHALL be authenticated after submitting valid credentials."
- **Invariant** — something observable that SHALL always hold while a condition obtains.
  _Example:_ "While an order is open, its line-item total SHALL equal the sum of its items."
- **Prohibition** — something observable that SHALL NOT occur.
  _Example:_ "The system SHALL NOT expose password hashes through any API response."
- **Precondition-consequence** — given a starting state, after a trigger, an observable result holds.
  _Example:_ "Given an expired session, when any authenticated request is made, the request SHALL be rejected."
- **Observable-state relationship** — a relationship between inputs and observable outputs that must hold over a class of cases.
  _Example:_ "For any query consisting of corpus-derived terms that score below the relevance threshold, the search SHALL return no results."

### 1.2 Authoring primitive

Before writing requirement text, answer: **what property must be true?**
Then express the property in one of the shapes above.

If you reach for a verb of action ("calls," "inserts," "queries," "assembles," "retries," "ranks by," "flags with"), you are describing mechanism.
Move it to `design.md` or `tasks.md` and return to state the property the mechanism was meant to produce.

A usable sentence stem, as guidance (not a template):

> The system SHALL {observable outcome} {when / whenever / if / for any} {condition on inputs or state}.

Adapt freely — contract shapes vary, and forcing every requirement into one grammar constrains expression.

**Lean toward universal claims where they apply.**
A claim of the form "for any query satisfying C, the system SHALL produce P" is stronger than "when the user submits query X, the system produces P" — universal claims surface gaps that example-shaped requirements hide, which is how the TF-IDF-style failure ("works on the scenarios, fails on the real corpus") gets caught at authoring time rather than in production.
See § 1.5 on how verification samples such claims.

### 1.3 Requirements describe WHAT; other artifacts describe HOW

| Artifact    | Answers                                  | Owns                                                                                                 |
| ----------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `spec.md`   | What must be true (the contract)         | Requirements, scenarios, observable behavior                                                         |
| `design.md` | How we achieve it, and why this approach | Chosen algorithms, heuristics, thresholds, data structures, strategies, retry policies, architecture |
| `tasks.md`  | What steps to execute                    | Atomic implementation actions in dependency order                                                    |

When drafting a spec sentence, ask which of the three artifacts owns it.
Named algorithms, thresholds, model choices, retry counts, similarity metrics, table schemas, and library choices belong in `design.md`.
Step sequences belong in `tasks.md`.
A spec sentence that survives stripping these is a contract; one that doesn't is not yet a requirement.

Early mechanism thinking has a legitimate home during spec authoring: the **Approach** section of `proposal.md` is the draft sandbox.
Park mechanism thoughts there as you write; formalize them into `design.md` after the contract stabilizes.

### 1.4 Protocol interfaces as contracts

When the spec describes a **published interface** that external consumers depend on — a public REST API, wire format, CLI, or message schema — the protocol details (status codes, endpoint paths, field names, flag names) are themselves observable outcomes.
Changing them breaks callers; they are contract, not mechanism.

The test: _does the detail form part of what external consumers depend on?_
If yes, it belongs in the spec.
If it is visible only to internal implementation, it is mechanism and belongs in `design.md`.

### 1.5 Scenarios are evidence, not definition

Every contract shape admits a space of cases.
Scenarios are concrete examples that illustrate and exercise the contract — not the contract itself.
A requirement should stand on its own as a claim; scenarios sample that claim.

Consequences:

1. **The requirement text must carry the contract.**
   If deleting all scenarios leaves nothing testable, the requirement is under-specified — the scenarios were carrying the contract.
2. **Scenarios should sample the space meaningfully.**
   Happy path alone is weak; include boundaries and cases where the property might plausibly fail.
3. **Universal claims need partition coverage when the input space splits.**
   See § 1.6 for the partition heuristic — when a universal SHALL's input space partitions along semantic lines the spec already names, scenarios must sample each partition; otherwise verification can only observe one arm of a multi-arm claim.

Verification in SDD samples these claims via scenarios and implementation tracing — it does not formally prove them.
Strong universal claims supported by thin, happy-path-only scenarios are a risk flag, not a fault.
Write the strongest claim you believe holds; select scenarios that would catch a plausible failure if the claim were violated.

### 1.6 Partition heuristic for universal claims

Universal claims ("for any X", "whenever Y", "the system SHALL ... for all ...") apply across a space of cases.
A single happy-path scenario only samples one corner of that space; verification has no way to observe the other arms.
This heuristic decides _when_ a universal claim needs multiple scenarios and _what those scenarios should partition along_ — without leaking mechanism into the spec.

**Question to ask of any universal SHALL claim**: _Does the requirement's subject reference named states, identities, or compositions that the rest of the spec already distinguishes?_

If yes → list partitions in scenarios, one scenario per partition the contract must hold for.
If no → a single scenario is fine.

**Four positive signals.**
Any one triggers the partition requirement.

1. **Outcome-conditioning lifecycle states.**
   The requirement's subject (Source, Manifest, Job, Session, etc.) has states defined or referenced elsewhere in the spec, _and_ the requirement's outcome is conditioned on which state holds.
   Partition: one scenario per outcome-relevant state.
   _Counter-example:_ "All requests SHALL be logged with user ID and timestamp" — the request has states (GET/POST, authenticated/unauthenticated), but the outcome (logged) does not depend on them; no partition needed.
2. **Identity / equivalence semantics.**
   The requirement involves "same as", "already seen", deduplication, normalization, or canonical form.
   Partition: `(novel input, equivalent-to-existing input)` at minimum.
3. **Multi-source composition.**
   The requirement's output is assembled from multiple producers the spec names.
   Partition: scenarios per producer combination, including disagreement cases (`both agree, A-only, B-only, A and B disagree`).
4. **Derived-pair invariants.**
   The requirement asserts `field_a == f(field_b)` or any relationship across two fields the spec names as related.
   Partition: one scenario per spec-asserted state of the data where the pair must hold, including any post-composition or post-merge state the spec describes.

**Negative signal** (no partition needed).
Subject has a single shape, no referenced lifecycle the outcome depends on, no identity/equivalence semantics, no multi-source merge, no derived pair.

**Anti-theater rule.**
If you can't name a partition without inventing one, the claim doesn't need partitions.
Don't manufacture branches to satisfy a checklist.

**Spec-author vocabulary test.**
Write the partition list using only vocabulary that already appears in the spec.
If you reach for implementation terms (write-site, code path, branch, function, module), you've crossed into mechanism — stop, and either rephrase in spec vocabulary or drop the partition.

**Where this heuristic is enforced.**

- `sdd-propose`, `sdd-translate`, `sdd-derive` apply it at spec-authoring time.
- `sdd-verify` applies it at verification time as the "partition-incomplete coverage" smell — when partitions are evident from the heuristic but scenarios cover only some, that is a WARNING distinct from "universal claim, single scenario."

## 2. RFC 2119 Keywords

Once the contract shape is clear, phrase it using RFC 2119 grammar.

| Keyword      | Meaning                                        |
| ------------ | ---------------------------------------------- |
| SHALL / MUST | Mandatory — no exceptions                      |
| SHOULD       | Recommended — exceptions require justification |
| MAY          | Optional — permitted but not required          |

- Use **SHALL** for non-negotiable system behaviors
- Use **MUST** for non-negotiable user/actor obligations
- Use **SHOULD** for strong recommendations
- Use **MAY** for optional behaviors

## 3. Baseline Spec Format

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

## 4. Delta Spec Format

Location: `.specs/changes/<name>/specs/<capability>/spec.md`

The delta format is about **provenance**, not authoring — ADDED/MODIFIED/REMOVED markers record how this change relates to the baseline.
Contract-shape rules from § 1 apply identically: each requirement (whether added, modified, or removed) is a contract statement.

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

## 5. Scenario Format

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
- Scenarios sample the contract stated in the requirement — they are evidence, not the contract itself (see § 1.5)
- Aim for scenarios that span happy path, boundary conditions, and plausible failure modes — not just the happy case

## 6. Calibration: Contracts vs. Mechanisms

A short reference of contract-statement rewrites, to calibrate intuition about the § 1 shapes.
These are not a checklist to audit against — they are illustrations of the artifact separation in § 1.3.

| Draft sentence (belongs elsewhere)                                                            | Contract statement (spec)                                                                                                                 | Where the mechanism goes          |
| --------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- |
| The system SHALL call `auth.verify()` when credentials are submitted.                         | The user SHALL be authenticated when valid credentials are submitted.                                                                     | `design.md` / `tasks.md`          |
| The system SHALL retry 3 times with exponential backoff.                                      | The system SHALL recover from transient upstream failures without user intervention.                                                      | `design.md` (retry policy)        |
| Below-threshold queries SHALL be assembled from bottom-quartile TF-IDF terms.                 | For any query consisting of corpus-derived terms that score below the relevance threshold, the search SHALL return no relevant documents. | `design.md` (generation strategy) |
| The recommender SHALL rank items by cosine similarity over embeddings.                        | The recommender SHALL return items ordered by relevance to the user's query, with the most relevant first.                                | `design.md` (similarity metric)   |
| Fraud detection SHALL flag transactions scoring above 0.8 on the gradient-boosted classifier. | Fraud detection SHALL flag transactions whose risk exceeds the acceptance threshold defined by the fraud policy.                          | `design.md` (model + cutoff)      |
