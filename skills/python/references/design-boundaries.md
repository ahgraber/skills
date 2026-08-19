# Design and Boundary Defaults

This reference explains the reasoning behind the audit checks for boundaries, contracts, and data flow.
Read it when proposing a fix for one of those findings, or when designing new module structure and you want the house default as a starting point.

## Functional Core / Imperative Shell

Business logic is easiest to test and reason about when it is pure.
The core is deterministic: the same inputs always produce the same outputs.
It performs no I/O — no network, no logging, no environment reads, no clock or randomness.
Anything external the logic needs (the current time, an ID, configuration, a random value) enters as a parameter.
The core returns plain data and decisions, never framework-bound types.

The shell is everything else.
It adapts external input into what the core accepts, and it carries out the effects the core decided on: persistence, network calls, logging, messaging.
The division of labor: the shell translates and routes; the core decides.

The payoff shows up in the tests.
Core logic gets heavy unit testing with no mocks, because there is nothing to mock.
Shell tests stay thin and focus on integration contracts.

## Module boundaries and ownership

A module owns its data, its invariants, and its internal structures.
Its persistence models and storage details stay private; other modules interact with it only through its explicit public interface.
Keep what crosses that interface to the minimum the use case requires, shaped as immutable DTO or value objects.
Shared mutable state across a boundary makes every consumer a suspect when an invariant breaks.

Each module is also the unit of immediate consistency.
Transactions stay inside one module; a transaction spanning two modules couples their failure modes and creates rollback complexity that no one owns.
Cross-module workflows coordinate through events, queued commands, or background jobs, and are eventually consistent by default.

During request handling, keep cross-module interactions orchestration-only: publish events, enqueue jobs, call infrastructure services such as auth, logging, and metrics.
The business decision stays in the handling module's core.
A synchronous domain call chain across modules turns one request into a distributed transaction.

Prefer a modular monolith with strict boundaries over a premature service split.
Well-kept module boundaries already provide the separation; extracting a service adds network failure modes and deployment coupling, and pays off only when team or organizational scaling demands it.

## Boundary contracts

Type every public function, method, and return value, and keep the annotations current when behavior changes.
A public signature is the contract, and static analysis can only enforce what it can see.

For parameters, accept the most abstract interface the function actually needs: `Mapping`, `Sequence`, or `Iterable` when the caller should not be forced to hand over one concrete, mutable type.
For returns, do the opposite: return a concrete type when its semantics (ordering, mutability, random access) are part of what the caller relies on.

Use `Protocol` for boundary-facing behavior contracts.
Structural subtyping keeps coupling low without requiring an inheritance relationship.
Add `@runtime_checkable` only when a runtime `isinstance` check is genuinely needed, and keep such checks out of hot paths.

Keep the module core's contracts on plain domain types.
Framework and schema types get adapted at the shell boundary, so a framework migration does not rewrite the domain.

## Pydantic at trust boundaries

Use pydantic where data crosses boundaries: request and response schemas, event and message payloads, external data ingress, and typed settings via `pydantic-settings`.
Keep internal transformations, tight loops, and domain logic that already operates on validated value objects on plain types; re-validating the same data adds overhead and couples the internals to the schema layer.

The boundary pattern has four steps:

1. Validate untrusted data at ingress with `model_validate` or a `TypeAdapter`, using strict mode when silent coercion would hide bugs.
2. Convert the validated data into domain-friendly structures.
3. Run domain behavior independent of transport and schema concerns.
4. Re-encode at egress with explicit output schemas via `model_dump`.

When validation fails, translate the `ValidationError` at the module boundary into a domain or application error with added context.
A raw pydantic exception crossing a module boundary leaks the schema layer into every caller.

## Contract evolution

Public contracts change in three ways, and each carries different risk.
Additive changes — new optional fields, new enum members, new endpoints or events — are safe by default.
Behavioral changes keep the shape but alter the semantics; they are the easiest to miss in review, so document them explicitly.
Breaking changes — removed or renamed fields, narrowed inputs, changed required fields or error contracts — require a versioning or migration plan before they ship.

For an intentional break, keep the old and new contracts side by side during the migration when practical.
Mark the deprecated path with a timeline and removal criteria; without them, the old contract stays supported indefinitely.

Every public contract change updates its contract tests: the happy path, the failure path, and serialization round-trip compatibility for schema changes.

## Composition and simplicity

Default to composition.
Inheritance couples the subclass to the parent's implementation, so reserve it for genuinely stable is-a relationships where substitution reduces glue code.

Build the minimal golden path that satisfies the contract before adding defense.
Add a defensive check when the failure mode is realistic and tested, not because an input might theoretically be wrong.

Do not extract an abstraction before the second or third concrete use.
The repetition shows where the real seam is, and an abstraction extracted too early is expensive to undo.
For the same reason, avoid `utils`/`common`/`shared` dumping grounds — a module without an owner accumulates coupling that nobody tracks.
