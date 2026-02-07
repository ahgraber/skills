# Contract Evolution

## Outcome

Public interface changes are deliberate, testable, and migration-safe.

## Change Categories

- Additive change: new optional fields/parameters, new enum members, new endpoints/events.
- Behavioral change: same shape, different semantics; treat as risky and document explicitly.
- Breaking change: removed/renamed fields, narrowed accepted inputs, changed required fields, changed error contracts.

## Compatibility Policy

- Preserve backward compatibility by default.
- For intentional breaks, require an explicit migration or versioning plan.
- Keep old and new contracts side by side during migration when practical.
- Mark deprecated paths with clear timelines and removal criteria.

## Review and Test Requirements

- Add or update contract tests for every public interface change.
- Assert both happy-path and failure-path behavior for changed contracts.
- Validate serialization/deserialization compatibility for schema changes.
- Confirm no persistence/framework internal types leak across module boundaries.
