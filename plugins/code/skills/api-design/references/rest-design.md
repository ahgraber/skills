# REST API Design

## Resource-Oriented Architecture

REST APIs are organized around **resources** (nouns), not actions (verbs).
HTTP methods provide the verbs.

### Resource Archetypes

Every URI in a REST API identifies one of four resource archetypes:

| Archetype      | What It Is                                                          | Naming Rule         | Example                                |
| -------------- | ------------------------------------------------------------------- | ------------------- | -------------------------------------- |
| **Document**   | A singular concept — like an object instance or record              | Singular noun       | `/leagues/seattle/teams/trebuchet`     |
| **Collection** | A server-managed directory of resources                             | Plural noun         | `/leagues/seattle/teams`               |
| **Store**      | A client-managed resource repository (client chooses URIs)          | Plural noun         | `PUT /users/a3f9c12d/favorites/alonso` |
| **Controller** | A procedural concept — an executable action with inputs and outputs | Verb or verb phrase | `POST /alerts/245743/resend`           |

**Controller resources** are the exception to the "nouns only" rule.
Use them for operations that cannot logically map to standard CRUD methods.
Controller names appear as the **last segment** in the URI path, with no child resources following them.

```text
POST /users/morgan/register           ✓ controller — action that isn't CRUD
POST /dbs/reindex                     ✓ controller — procedural operation
POST /orders/{id}/cancel              ✓ controller — can't be modeled as a simple state field

GET  /getUsers                        ✗ verb used where a collection noun belongs
POST /createOrder                     ✗ verb duplicates what POST already means
```

Before reaching for a controller, try modeling the operation as:

1. A **state transition** — `PATCH /orders/{id}` with `{"status": "cancelled"}`
2. A **sub-resource** — `POST /orders/{id}/cancellation` (treats the action result as a created resource)

Use a controller (option 3) when the operation is procedural, has side effects beyond the target resource, or doesn't produce a resource that clients would later GET.

### HTTP Method Semantics

| Method    | Purpose                                 | Idempotent                    | Safe | Typical Status Codes                   |
| --------- | --------------------------------------- | ----------------------------- | ---- | -------------------------------------- |
| `GET`     | Read resource(s)                        | Yes                           | Yes  | 200, 404                               |
| `POST`    | Create resource                         | No                            | No   | 201 (with `Location` header), 400, 409 |
| `PUT`     | Replace resource entirely               | Yes                           | No   | 200, 204, 404                          |
| `PATCH`   | Partial update                          | It depends on patch semantics | No   | 200, 204, 404                          |
| `DELETE`  | Remove resource                         | Yes                           | No   | 204, 404                               |
| `HEAD`    | Headers only (same as GET without body) | Yes                           | Yes  | 200, 404                               |
| `OPTIONS` | Supported methods/capabilities          | Yes                           | Yes  | 200, 204                               |

\*PATCH may be idempotent or non-idempotent depending on the patch format and operation semantics. `If-Match` + ETag helps prevent lost updates, but it is a concurrency control mechanism rather than a blanket idempotency guarantee.

### CRUD Endpoint Layout

```text
GET    /users              → List users (paginated)
POST   /users              → Create user
GET    /users/{id}         → Get single user
PUT    /users/{id}         → Replace user
PATCH  /users/{id}         → Partial update user
DELETE /users/{id}         → Delete user
```

### Nested Resources

Use nesting to express parent-child relationships, but **limit to 2 levels**:

```text
GET  /users/{userId}/orders              → User's orders
GET  /users/{userId}/orders/{orderId}    → Specific order
POST /users/{userId}/orders              → Create order for user
```

Beyond 2 levels, return URIs in response bodies instead:

```json
{
  "id": "order-123",
  "items": "/orders/order-123/items",
  "shipping": "/orders/order-123/shipping"
}
```

## Request Design

### Content Negotiation

- Accept `Content-Type: application/json` for request bodies
- Return `Content-Type: application/json` in responses
- Support `Accept` header for format negotiation when needed
- Use `application/merge-patch+json` for PATCH when appropriate (RFC 7396)

### Idempotency

For non-idempotent operations (especially payments, transfers), support the `Idempotency-Key` header:

```text
POST /payments
Idempotency-Key: a1b2c3d4-e5f6-7890
Content-Type: application/json

{"amount": 100, "currency": "USD", "recipient": "user-456"}
```

Server stores the result keyed by `Idempotency-Key` and returns the cached result on duplicate requests.

### Conditional Requests

Use ETags for optimistic concurrency and cache validation:

```text
GET /users/123
→ ETag: "v1-abc123"

PUT /users/123
If-Match: "v1-abc123"
→ 200 OK (updated) or 412 Precondition Failed (stale)

GET /users/123
If-None-Match: "v1-abc123"
→ 304 Not Modified (cache hit) or 200 OK (new data)
```

## API Surface Is Not Database Surface

Your API contract and your database schema serve different masters.
The API serves consumers; the schema serves storage.
Coupling them looks easy at first and becomes expensive fast.

### Why This Matters

1. **Breaking changes propagate silently.**
   Renaming a DB column (`birth_day` → `birthday`) instantly breaks every client if the API auto-maps fields.
   With a mapping layer, the API keeps returning `birth_day` regardless of the internal rename.

2. **Sensitive data leaks by default.**
   Auto-serializing entities exposes fields like `password_hash`, internal flags, or soft-delete markers unless you remember to exclude them — an opt-out model that fails under pressure.

3. **Business logic migrates to clients.**
   If your API returns raw join tables, clients must reassemble domain concepts themselves, duplicating logic across every consumer.
   Zalando's guidelines warn that "thin database wrappers tend to shift business logic to the clients."

4. **Independent evolution becomes impossible.**
   You cannot split tables, change storage engines, or denormalize for performance without an API release.
   Google's API Design Guide states: "having an API that is identical to the underlying database schema is actually an anti-pattern, as it tightly couples the surface to the underlying system."

5. **CRUD-per-table forces wrong transaction boundaries.**
   Mirroring CRUD onto endpoints (`POST /items`, `POST /payments` individually) forces distributed coordination.
   Designing around domain operations (`POST /orders` with items and payment as a batch) eliminates race conditions and partial-failure complexity.

### Anti-Patterns

| Anti-Pattern                                  | Risk Level                                                                               | Problem                                                     |
| --------------------------------------------- | ---------------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| Auto-serializing ORM entities to JSON         | High for public/multi-consumer APIs; low for internal-only MVPs where you own both sides | Leaks internals, breaks on schema changes                   |
| One REST resource per DB table                | High                                                                                     | Forces clients to do joins; N+1 API calls                   |
| Exposing surrogate keys (`id: 47`)            | Medium–High                                                                              | Ties clients to DB-generated IDs; leaks ordering and volume |
| Returning all columns by default              | High                                                                                     | Over-fetching; security risk                                |
| DB enum values in API responses (`status: 1`) | High                                                                                     | Internal storage representation leaks into contract         |

### How to Decouple

**Use a dedicated mapping layer** — DTOs, serializers, or view models — inside the service layer, not in controllers.

```text
DB entity (internal)              API representation (contract)
─────────────────────             ──────────────────────────────
users.first_name          →       { "name": "Alice Smith" }
users.last_name           ↗
users.password_hash                (omitted)
users.is_deleted                   (omitted)
users.created_at          →       { "joined": "2024-03-15" }
orders.user_id (FK)       →       { "customer": "/users/abc-123" }
```

**Key rules:**

- **Separate DTOs per operation** — `CreateUserRequest`, `UserResponse`, `UserSummary` — not one object for everything.
  Different operations need different shapes; a creation request shouldn't carry an `id`, and a list response shouldn't carry every detail.
- **Map in the service layer**, not the controller.
  Controllers stay thin; the service layer owns the translation between domain and contract.
- **Treat the API shape as a versioned contract.**
  Use OpenAPI/JSON Schema as the source of truth.
  The DB schema is free to change behind the mapping layer.
- **Use opaque identifiers.**
  UUIDs or slugs instead of sequential integers.
  Pagination cursors should be opaque tokens, never raw DB offsets or IDs.

## Response Design

### Consistent Envelope (Optional)

Some APIs use one; others return data directly.
Pick one and be consistent:

**Direct (recommended for simple APIs):**

```json
[
  {
    "id": "1",
    "name": "Alice"
  },
  {
    "id": "2",
    "name": "Bob"
  }
]
```

**Envelope (recommended when metadata is needed):**

```json
{
  "data": [
    {
      "id": "1",
      "name": "Alice"
    },
    {
      "id": "2",
      "name": "Bob"
    }
  ],
  "meta": {
    "total": 42,
    "page": 1,
    "per_page": 20
  }
}
```

### HATEOAS (Hypermedia as the Engine of Application State)

Include links to related resources and available actions:

```json
{
  "id": "order-123",
  "status": "pending",
  "_links": {
    "self": {
      "href": "/orders/order-123"
    },
    "cancel": {
      "href": "/orders/order-123/cancel",
      "method": "POST"
    },
    "items": {
      "href": "/orders/order-123/items"
    },
    "customer": {
      "href": "/users/user-456"
    }
  }
}
```

HATEOAS makes APIs self-discoverable but adds complexity.
Use it when clients benefit from dynamic navigation (e.g., workflow-driven UIs).
Skip it for simple internal APIs.

### Caching

- Set `Cache-Control` headers on GET responses: `Cache-Control: public, max-age=300`
- Use `ETag` and `Last-Modified` for conditional requests
- Distinguish `public` (CDN-cacheable) from `private` (user-specific) responses
- Use `Vary` header when responses differ by request headers (e.g., `Vary: Accept, Authorization`)

## Long-Running Operations

Not all operations complete synchronously.
When processing takes more than a few seconds, use an asynchronous job pattern:

1. **Accept the request** — return `202 Accepted` immediately with a job resource URI:

   ```text
   POST /reports/generate
   → 202 Accepted
      Location: /jobs/report-abc123
   ```

2. **Poll for status** — clients `GET` the job resource:

   ```json
   GET /jobs/report-abc123
   → 200 OK
   {
     "id": "report-abc123",
     "status": "processing",
     "progress": 42,
     "created_at": "2024-03-15T10:00:00Z",
     "estimated_completion": "2024-03-15T10:02:00Z"
   }
   ```

3. **Return the result** — once complete, either redirect to the result resource or embed it:

   ```json
   GET /jobs/report-abc123
   → 200 OK
   {
     "id": "report-abc123",
     "status": "complete",
     "result": "/reports/2024-Q1"
   }
   ```

4. **Handle failure** — surface `"status": "failed"` with an error body, not a successful status code.

**When to apply:**

- Database-heavy exports or aggregations
- External service calls (email sends, third-party processing)
- Any operation where P99 latency exceeds client timeout budgets

For real-time progress, prefer WebSockets or SSE over aggressive polling.

## Security Checklist

- **HTTPS everywhere** — no exceptions
- **Authentication** via Bearer tokens (JWT, OAuth 2.0) or API keys in headers (never in URLs)
- **Authorization** checked at the business logic layer, not just the route level
- **Rate limiting** with `429 Too Many Requests` and `Retry-After` header
- **Input validation** — reject unexpected fields, enforce types and constraints
- **No internal details in errors** — never expose stack traces, SQL errors, or file paths
- **CORS** configured to allow only expected origins
- **Principle of least privilege** — each API key/token grants minimum necessary access

## OpenAPI Specification

For non-trivial REST APIs, maintain an OpenAPI 3.1 spec:

- Define all endpoints, request/response schemas, and error responses
- Include `examples` for every endpoint
- Use `$ref` for shared components (schemas, parameters, responses)
- Validate with `npx @redocly/cli lint openapi.yaml`
- Generate mock servers with `npx @stoplight/prism-cli mock openapi.yaml`
- Version-control the spec alongside the code

## Further Reading

- Mark Massé, _REST API Design Rulebook_ (O'Reilly, 2011) — resource archetypes, URI naming rules, and controller resources
- [Microsoft Azure REST API Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md)
- [Google API Design Guide](https://docs.cloud.google.com/apis/design)
- [Google AIP-121, Resource-oriented design](https://google.aip.dev/121)
- [Google AIP-136, Custom methods](https://google.aip.dev/136)
- [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/)
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
