# Data and State Lifecycle

## Outcome

Clear ownership and predictable data flow from ingress to persistence/egress.

## Lifecycle Flow

1. Ingress at shell boundary: receive untrusted external input.
2. Validation: enforce schema and required fields at ingress.
3. Normalization: convert input to stable internal structures/value objects.
4. Domain decisions: run pure logic on normalized internal data.
5. Persistence and egress: map domain data to storage or transport schemas explicitly.

## Ownership Rules

- Each module owns its data invariants.
- Keep persistence schemas and ORM models private to the owning module.
- Cross-module interaction must use explicit public interfaces.

## Sharing and Mutability Rules

- Share the minimum data required through DTO/value objects.
- Prefer immutable or read-only data shapes for cross-boundary exchange.
- Minimize shared mutable state.
- Isolate stateful adapters at shell boundaries.

## State Transition Reliability

- Validate before mutating state whenever possible.
- Make state transitions explicit and idempotent where retries can occur.
- Persist enough transition context for replay and failure diagnosis.
