# Evidence-Class Taxonomy

Tags attached to observer entries that drive lift discipline.
The lifter applies per-tag rules; multi-tag observations compose rules per the table below.

## Canonical set

7 named tags + custom string fallthrough.
Flat enum.
Multi-tag allowed on a single observation.
The lifter composes rules; rules are designed to compose without conflict.

| Tag                    | One-line trigger                                                                        | Provenance default |
| ---------------------- | --------------------------------------------------------------------------------------- | ------------------ |
| `algorithmic`          | A specific algorithm, threshold, or hand-tuned constant produces an observable property | ON                 |
| `security`             | Auth, crypto, secrets, access control, or attack-surface validation                     | **OFF (opt-in)**   |
| `reliability`          | Error handling, retries, fallbacks, timeouts, idempotency guarantees                    | ON                 |
| `external_surface`     | Call/write to a non-owned API, schema, topic, or file format                            | ON                 |
| `state_coupling`       | Shared mutable state crossing capability boundaries (DB rows, cache keys, files)        | ON                 |
| `framework_recognized` | Code maps to a known framework pattern (Django Model, FastAPI route, Spring DI)         | ON                 |
| `public_api`           | Code defines a publicly-consumed interface (HTTP/gRPC/CLI/library/module export)        | ON                 |

Untagged observations get default lift discipline — translate "what code does" to "what property the code maintains."

## Per-tag definitions

### `algorithmic`

- **Observer applies when:** the observed behavior is produced by a specific algorithm, threshold, scoring rule, or hand-tuned constant — and the property the user cares about is a _consequence_ of that algorithm, not the algorithm itself.
- **Lift rule:** do not promote the algorithm to a contract.
  Apply the strategy check:
  - If the algorithm is the _intended strategy_ (e.g., the system is _defined_ by using PageRank): lift the property AND record the algorithm verbatim as a strategy note.
    Emit an Uncertainty asking the user to confirm strategy ownership.
  - If the algorithm is an _internal optimization_ (e.g., TF-IDF as one of many possible relevance scorers): lift only the property ("ranked by relevance").
    Emit an Uncertainty asking the user to confirm that the algorithm is replaceable.
  - Either way, surface the choice — never silently freeze.
- **Validate:** list all algorithm-related Uncertainties for user disposition.
- **Composition:** dominant for lift output.
  Combined with `external_surface` (e.g., a 3rd-party API specifies the algorithm), preserve the algorithm verbatim under External System Exception AND emit Uncertainty.
- **Example signals:** `tfidf_score > 0.3`; `decay_factor=0.85`; `PriorityQueue with custom compare`; specific retry backoff curves.

### `security`

- **Observer applies when:** the code involves authentication, authorization, cryptography, secret handling, access control, input validation against injection/XSS/SSRF/path traversal, or rate limiting against abuse.
- **Lift rule:** lift to _strong specificity_.
  Not "SHALL enforce access control" but "SHALL deny non-admin users from modifying foreign user records."
  Name the actor, the resource, and the predicate explicitly.
- **Provenance default:** **OFF.**
  File:line references in observations can leak the location of crypto verification, secret handling, or auth checks.
  Opt-in retention with explicit warning.
- **Validate:** emit a security-tagged section in the validate report; user confirms before output.
- **Composition:** provenance-OFF wins regardless of other tags.
  Other tags' lift rules still apply (a `[security, external_surface]` observation produces a strong-specificity contract that preserves the external auth interface verbatim).
- **Example signals:** `hmac.compare_digest`; password hashing functions; `@requires_role`; SQL parameterization; rate-limit decorators.

### `reliability`

- **Observer applies when:** the code involves error handling, retries, fallbacks, timeouts, circuit breakers, deduplication, idempotency keys, or recovery sequences.
- **Lift rule:** required to produce explicit scenarios for failure paths.
  Not "SHALL handle errors" but a `**WHEN** call fails / **THEN** retry up to N / **THEN** if retries exhausted, surface to caller without state corruption` scenario.
  Include the recovery property explicitly.
- **Validate:** flag findings tagged `reliability` whose lifted contract has no failure scenario.
- **Composition:** combines with `external_surface` (retry on external call); with `state_coupling` (recovery without corruption).
- **Example signals:** `tenacity.retry`; `try/except` with rollback; idempotency keys; circuit breakers; `with timeout()`.

### `external_surface`

- **Observer applies when:** the observation involves a call to a 3rd-party API, a write to a schema not owned by this codebase, a message bus topic with consumers outside this codebase, or production of a file format defined externally (CSV with externally-specified columns, JSON conforming to OpenAPI from a vendor, etc.).
- **Lift rule:** apply External System Exception.
  Preserve the interface verbatim (endpoint, table columns, topic name, message schema) alongside the property.
  Example: "SHALL persist user state to the shared `users` table with columns `id`, `email`, `created_at`" — not just "SHALL persist user state."
- **Validate:** cross-check tagged observations against external-surface candidates from discovery.
  Warn on mismatch (observer tagged something not flagged in discovery, or vice versa).
- **Composition:** combines with `reliability` (retry policy on external call); with `security` (3rd-party auth APIs); with `state_coupling` (shared external state).
- **Example signals:** `stripe.charges.create`; Kafka `producer.send`; OpenAPI-generated client calls; database writes to a schema in `vendor/`.

### `state_coupling`

- **Observer applies when:** the observation involves shared mutable state crossing capability boundaries — same DB row written by multiple capabilities, same cache key, same file path, shared global, message topic with internal consumers.
- **Lift rule:** name the shared resource and lift invariants about it (write order, read consistency, partition tolerance, idempotency of overwrites).
  The shared resource appears in the contract.
- **Validate:** ensure the resource is named in the contract, not just hinted.
- **Composition:** combines with `external_surface` if state lives in a 3rd-party system (then preserve external schema verbatim AND name invariants).
- **Example signals:** `db.users.update` from multiple services; `redis.set("session:*")` from auth and from session-management; shared config-file writes.

### `framework_recognized`

- **Observer applies when:** the code matches a recognized framework pattern (Django Model declaration; FastAPI route decorator; Spring DI registration; NestJS module/controller; Rails ActiveRecord; SQLAlchemy declarative).
- **Lift rule:** lift framework-derived contracts, not literal-code contracts. `class User(Model): name = CharField()` → "Users SHALL have a name attribute available for create/read/update per Django ORM lifecycle" (the _meaning_ of declaring a Model field), not "User SHALL declare a name field."
- **Composition:** background context; if combined with `security` (framework auth middleware), security rules dominate.
  The framework name lives in `signals` so the lifter knows which lens to apply.
- **Example signals:** `django_model_declaration`; `fastapi_route`; `nestjs_controller`; `sqlalchemy_declarative`.

### `public_api`

- **Observer applies when:** the code defines a publicly-consumed interface — HTTP/gRPC/GraphQL endpoint, CLI command/flag set, library export, or a module's public API consumed by other modules within the codebase.
- **Lift rule:** preserve interface details as part of the contract — route + method + request/response shape, CLI command + flag semantics, exported symbol + signature, module's public function set.
  The interface IS the contract; do not abstract it away.
- **Validate:** cross-check tagged observations against the port/interface inventory from discovery.
  Warn on mismatch.
- **Composition:**
  - With `external_surface` for _bridging_ code (webhook receivers, gateway services, library facades that expose external services to internal callers).
    Both apply; both shapes preserved.
  - With `security` for auth-protected endpoints; security's strong-specificity rule sharpens the public-API contract.
  - With `state_coupling` for endpoints that mutate shared state; the contract names both the interface and the shared resource invariants.
  - With `reliability` for endpoints with retry/idempotency guarantees.
- **Layer signals:** `http_route`, `grpc_method`, `cli_command`, `library_export`, `module_export`. `module_export` distinguishes internal-public from external-public; the lifter treats both with the same preservation rule, but validate may apply different stringency (external-public deserves explicit deprecation policy; module-public is more refactorable).

## Composition rules

When multiple tags apply to one observation:

1. **`algorithmic` is dominant on lift output.**
   Uncertainty emission cannot be suppressed by other tags.
2. **`security` is dominant on provenance.**
   Provenance-OFF wins regardless.
   Other tags' lift rules still apply.
3. **`external_surface` + `state_coupling`** — both apply; the contract names both the external interface and the shared-resource invariants.
4. **`reliability`** modifies whatever else applies; never replaces.
5. **`framework_recognized`** is background lens; never overrides another tag's rule.
6. **Unknown / custom tags** — lifter emits an Uncertainty with the tag name, asking the user for guidance.
   Don't drop, don't guess.

## Custom tags

Observers may emit tags outside the canonical set when a finding genuinely doesn't fit.
The lifter treats unknown tags by applying default lift discipline AND emitting a brief Uncertainty noting the tag name.
This preserves the signal without forcing the lifter to guess at unspecified rules.

If a custom tag recurs across runs, promote it to the canonical set and document its rule here.
