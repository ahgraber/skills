# Clarification Taxonomy

Use this taxonomy to build the internal ambiguity coverage map for `spec.md`.
For each category, classify status as:

- `Clear`: sufficient and testable as written.
- `Partial`: present but ambiguous, incomplete, or not measurable.
- `Missing`: not present where it is needed.

## Functional Scope and Behavior

- Core user goals and success criteria
- Explicit out-of-scope declarations
- User roles/personas differentiation

## Domain and Data Model

- Entities, attributes, relationships
- Identity and uniqueness rules
- Lifecycle/state transitions
- Data volume/scale assumptions

## Interaction and UX Flow

- Critical user journeys/sequences
- Error/empty/loading states
- Accessibility or localization notes

## Non-Functional Quality Attributes

- Performance (latency/throughput targets)
- Scalability (horizontal/vertical limits)
- Reliability and availability (uptime/recovery expectations)
- Observability (logging/metrics/tracing signals)
- Security and privacy (authN/Z, data protection, threat assumptions)
- Compliance/regulatory constraints

## Integration and External Dependencies

- External services/APIs and failure modes
- Data import/export formats
- Protocol/versioning assumptions

## Edge Cases and Failure Handling

- Negative scenarios
- Rate limiting/throttling
- Conflict resolution (for example concurrent edits)

## Constraints and Tradeoffs

- Technical constraints (language, storage, hosting)
- Explicit tradeoffs or rejected alternatives

## Terminology and Consistency

- Canonical glossary terms
- Avoided synonyms/deprecated terms

## Completion Signals

- Acceptance criteria testability
- Measurable Definition of Done style indicators

## Misc and Placeholders

- TODO markers/unresolved decisions
- Ambiguous adjectives lacking quantification (for example robust, intuitive)
