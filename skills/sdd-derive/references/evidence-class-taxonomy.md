# Evidence-Class Taxonomy

Tags attached to observer entries that drive lift discipline.
Multi-tag is allowed and expected; rules compose without conflict.

## Canonical set

Seven named tags + custom string fallthrough.
Untagged observations get default lift discipline: translate "what code does" to "what property the code maintains."

| Tag                    | Trigger                                                                                 | Provenance default |
| ---------------------- | --------------------------------------------------------------------------------------- | ------------------ |
| `algorithmic`          | A specific algorithm, threshold, or hand-tuned constant produces an observable property | ON                 |
| `security`             | Auth, crypto, secrets, access control, or attack-surface validation                     | **OFF (opt-in)**   |
| `reliability`          | Error handling, retries, fallbacks, timeouts, idempotency guarantees                    | ON                 |
| `external_surface`     | Call/write to a non-owned API, schema, topic, or file format                            | ON                 |
| `state_coupling`       | Shared mutable state crossing capability boundaries (DB rows, cache keys, files)        | ON                 |
| `framework_recognized` | Code maps to a known framework pattern (Django Model, FastAPI route, Spring DI)         | ON                 |
| `public_api`           | Code defines a publicly-consumed interface (HTTP/gRPC/CLI/library/module export)        | ON                 |

## Per-tag rules

### `algorithmic`

- **Apply when:** observed behavior is produced by a specific algorithm, threshold, scoring rule, or hand-tuned constant — and the user-facing property is a _consequence_ of that algorithm, not the algorithm itself.
- **Lift rule:** do not promote the algorithm to a contract.
  Apply the strategy check:
  - _Intended strategy_ (e.g., system is _defined_ by using PageRank): lift the property AND record the algorithm verbatim as a strategy note.
    Emit Uncertainty asking the user to confirm strategy ownership.
  - _Internal optimization_ (e.g., TF-IDF as one of many possible relevance scorers): lift only the property.
    Emit Uncertainty asking the user to confirm replaceability.
- **Validate:** list all algorithm-related Uncertainties for user disposition.
- **Combine with `external_surface`** (3rd-party API specifies the algorithm): preserve verbatim under External System Exception AND emit Uncertainty.
- **Example signals:** `tfidf_score > 0.3`; `decay_factor=0.85`; `PriorityQueue with custom compare`; specific retry backoff curves.

### `security`

- **Apply when:** auth, authorization, cryptography, secret handling, access control, input validation against injection/XSS/SSRF/path traversal, or rate limiting against abuse.
- **Lift rule:** lift to _strong specificity_.
  Name actor, resource, predicate.
  Not "SHALL enforce access control" but "SHALL deny non-admin users from modifying foreign user records."
- **Provenance default OFF.**
  File:line references can leak crypto/secret/auth locations.
  Opt-in retention requires explicit warning.
- **Validate:** emit a security-tagged section in the report; user confirms before output.
- **Example signals:** `hmac.compare_digest`; password hashing functions; `@requires_role`; SQL parameterization; rate-limit decorators.

### `reliability`

- **Apply when:** error handling, retries, fallbacks, timeouts, circuit breakers, deduplication, idempotency keys, recovery sequences.
- **Lift rule:** produce explicit failure-path scenarios; include the recovery property explicitly.
  Not "SHALL handle errors" but `**WHEN** call fails / **THEN** retry up to N / **THEN** if exhausted, surface to caller without state corruption`.
- **Validate:** flag tagged findings whose lifted contract has no failure scenario.
- **Combine with** `external_surface` (retry on external call); `state_coupling` (recovery without corruption).
- **Example signals:** `tenacity.retry`; `try/except` with rollback; idempotency keys; circuit breakers; `with timeout()`.

### `external_surface`

- **Apply when:** call to a 3rd-party API, write to a schema not owned by this codebase, message bus topic with consumers outside, or production of an externally-defined file format.
- **Lift rule:** apply External System Exception.
  Preserve the interface verbatim (endpoint, columns, topic name, schema) alongside the property.
  Example: "SHALL persist user state to the shared `users` table with columns `id`, `email`, `created_at`" — not just "SHALL persist user state."
- **Validate:** cross-check against external-surface candidates from discovery; warn on mismatch.
- **Combine with** `reliability` (retry policy); `security` (3rd-party auth); `state_coupling` (shared external state).
- **Example signals:** `stripe.charges.create`; Kafka `producer.send`; OpenAPI-generated client calls; writes to a `vendor/` schema.

### `state_coupling`

- **Apply when:** shared mutable state crosses capability boundaries — same DB row written by multiple capabilities, same cache key, same file path, shared global, message topic with internal consumers.
- **Lift rule:** name the shared resource and lift invariants about it (write order, read consistency, partition tolerance, idempotency of overwrites).
  The shared resource appears in the contract.
- **Validate:** ensure the resource is named, not just hinted.
- **Combine with** `external_surface` if state lives in a 3rd-party system (preserve external schema verbatim AND name invariants).
- **Example signals:** `db.users.update` from multiple services; `redis.set("session:*")` from auth and session-management; shared config-file writes.

### `framework_recognized`

- **Apply when:** code matches a recognized framework pattern (Django Model; FastAPI route decorator; Spring DI; NestJS module/controller; Rails ActiveRecord; SQLAlchemy declarative).
- **Lift rule:** lift framework-derived contracts, not literal-code contracts. `class User(Model): name = CharField()` → "Users SHALL have a name attribute available for create/read/update per Django ORM lifecycle" (the _meaning_), not "User SHALL declare a name field."
- **Background lens:** framework name lives in `signals` so the lifter knows which lens to apply.
  If combined with `security` (framework auth middleware), security rules dominate.
- **Example signals:** `django_model_declaration`; `fastapi_route`; `nestjs_controller`; `sqlalchemy_declarative`.

### `public_api`

- **Apply when:** code defines a publicly-consumed interface — HTTP/gRPC/GraphQL endpoint, CLI command/flag set, library export, or a module's public API consumed by other modules within the codebase.
- **Lift rule:** preserve interface details as part of the contract — route + method + request/response shape, CLI command + flag semantics, exported symbol + signature, module's public function set.
  The interface IS the contract; do not abstract it away.
- **Validate:** cross-check against the port/interface inventory from discovery; warn on mismatch.
- **Combine with:**
  - `external_surface` for _bridging_ code (webhooks, gateways, library facades).
    Preserve both shapes.
  - `security` for auth-protected endpoints; security's strong-specificity sharpens the public-API contract.
  - `state_coupling` for endpoints that mutate shared state; contract names both interface and resource invariants.
  - `reliability` for endpoints with retry/idempotency guarantees.
- **Layer signals:** `http_route`, `grpc_method`, `cli_command`, `library_export`, `module_export`. `module_export` distinguishes internal-public from external-public; same preservation rule, but validate may apply different stringency (external-public deserves explicit deprecation policy; module-public is more refactorable).

## Composition rules

When multiple tags apply, resolve in this order:

1. **`algorithmic` dominates lift output.**
   Uncertainty emission cannot be suppressed.
2. **`security` dominates provenance.**
   Provenance-OFF wins.
   Other tags' lift rules still apply.
3. **`external_surface` + `state_coupling`** — both apply; contract names both the external interface and the shared-resource invariants.
4. **`reliability`** modifies whatever else applies; never replaces.
5. **`framework_recognized`** is background lens; never overrides another tag's rule.
6. **Unknown / custom tags** — lifter emits an Uncertainty with the tag name; applies default lift discipline; does not guess.

## Custom tags

Observers may emit tags outside the canonical set when a finding genuinely doesn't fit.
The lifter applies default lift discipline AND emits a brief Uncertainty noting the tag name.
This preserves the signal without forcing a guess.

If a custom tag recurs, promote it to the canonical set and document its rule here.
