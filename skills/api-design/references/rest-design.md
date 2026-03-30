# REST API Design

## Resource-Oriented Architecture

REST APIs are organized around **resources** (nouns), not actions (verbs).
HTTP methods provide the verbs.

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

## Response Design

### Consistent Envelope (Optional)

Some APIs use a response envelope; others return data directly.
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

### HATEOAS (Hypermedia)

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

- [Microsoft Azure REST API Guidelines](https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md)
- [Google API Design Guide](https://docs.cloud.google.com/apis/design)
- [Google AIP-121, Resource-oriented design](https://google.aip.dev/121)
- [Google AIP-136, Custom methods](https://google.aip.dev/136)
- [Zalando RESTful API Guidelines](https://opensource.zalando.com/restful-api-guidelines/)
- [OpenAPI Specification](https://spec.openapis.org/oas/latest.html)
