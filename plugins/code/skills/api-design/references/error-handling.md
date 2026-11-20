# API Error Handling

## HTTP Status Code Reference

### 2xx Success

| Code             | Meaning           | When to Use                           |
| ---------------- | ----------------- | ------------------------------------- |
| `200 OK`         | Request succeeded | GET, PUT, PATCH with response body    |
| `201 Created`    | Resource created  | POST; include `Location` header       |
| `204 No Content` | Success, no body  | DELETE, PUT/PATCH when no body needed |

### 4xx Client Errors

| Code                         | Meaning                                   | When to Use                                              |
| ---------------------------- | ----------------------------------------- | -------------------------------------------------------- |
| `400 Bad Request`            | Malformed request or generic client error | Invalid JSON, unsupported parameters, type mismatches    |
| `401 Unauthorized`           | Not authenticated                         | Missing or invalid credentials                           |
| `403 Forbidden`              | Authenticated but not authorized          | Valid credentials, insufficient permissions              |
| `404 Not Found`              | Resource does not exist                   | Invalid ID, deleted resource                             |
| `405 Method Not Allowed`     | HTTP method not supported                 | `DELETE` on a read-only resource                         |
| `409 Conflict`               | State conflict                            | Duplicate creation, optimistic lock failure              |
| `410 Gone`                   | Resource permanently removed              | Deprecated endpoint past sunset date                     |
| `412 Precondition Failed`    | `If-Match` / `If-Unmodified-Since` failed | Stale ETag in conditional update                         |
| `415 Unsupported Media Type` | Wrong `Content-Type`                      | XML sent to JSON-only endpoint                           |
| `422 Unprocessable Entity`   | Semantically invalid                      | Well-formed JSON but validation or business rule failure |
| `429 Too Many Requests`      | Rate limited                              | Always include `Retry-After` header                      |

### 5xx Server Errors

| Code                        | Meaning                           | When to Use                               |
| --------------------------- | --------------------------------- | ----------------------------------------- |
| `500 Internal Server Error` | Unhandled server failure          | Generic catch-all; never throw explicitly |
| `502 Bad Gateway`           | Upstream service failure          | Proxy/gateway received invalid response   |
| `503 Service Unavailable`   | Temporary overload or maintenance | Include `Retry-After` header              |
| `504 Gateway Timeout`       | Upstream service timeout          | Proxy/gateway timed out waiting           |

## Error Response Format — RFC 9457 Problem Details

Use RFC 9457 "Problem Details for HTTP APIs" (`application/problem+json`) for structured error responses.
RFC 9457 obsoletes RFC 7807 (2023); use 9457 for new work.

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "The request body contains invalid fields.",
  "instance": "/users/123",
  "errors": [
    {
      "field": "email",
      "message": "Must be a valid email address",
      "code": "INVALID_EMAIL"
    },
    {
      "field": "age",
      "message": "Must be at least 18",
      "code": "MIN_VALUE",
      "meta": {
        "minimum": 18,
        "actual": 15
      }
    }
  ],
  "request_id": "req-abc-123",
  "timestamp": "2024-03-15T10:30:00Z"
}
```

### Required fields

| Field    | Purpose                                                            |
| -------- | ------------------------------------------------------------------ |
| `type`   | URI reference identifying the error type (stable, documented)      |
| `title`  | Short human-readable summary (same for all instances of this type) |
| `status` | HTTP status code (integer)                                         |
| `detail` | Human-readable explanation specific to this occurrence             |

### Recommended extensions

| Field               | Purpose                                                 |
| ------------------- | ------------------------------------------------------- |
| `instance`          | URI of the resource that generated the error            |
| `errors`            | Array of field-level validation errors                  |
| `request_id`        | Correlation ID for debugging (log this server-side too) |
| `timestamp`         | ISO 8601 timestamp                                      |
| `documentation_url` | Link to docs explaining this error type                 |

## Validation Errors

For requests with multiple invalid fields, return **all** validation errors at once (not just the first one).
Use either `400` or `422` consistently for this category and document the choice:

```json
{
  "type": "https://api.example.com/errors/validation-error",
  "title": "Validation Error",
  "status": 400,
  "detail": "2 validation errors in request body.",
  "errors": [
    {
      "field": "name",
      "message": "Required field",
      "code": "REQUIRED"
    },
    {
      "field": "email",
      "message": "Invalid format",
      "code": "INVALID_FORMAT"
    }
  ]
}
```

Each error in the array should have:

- `field` — dot-notated path to the invalid field (e.g., `address.zip_code`)
- `message` — human-readable description
- `code` — machine-readable error code (stable, documented)

## Retryability

Help clients decide whether to retry:

### Retryable errors

| Code                        | Retry Strategy                      |
| --------------------------- | ----------------------------------- |
| `408 Request Timeout`       | Immediate retry (once)              |
| `429 Too Many Requests`     | Wait for `Retry-After` header value |
| `500 Internal Server Error` | Exponential backoff                 |
| `502 Bad Gateway`           | Exponential backoff                 |
| `503 Service Unavailable`   | Wait for `Retry-After` header value |
| `504 Gateway Timeout`       | Exponential backoff                 |

### Non-retryable errors

`400`, `401`, `403`, `404`, `405`, `409`, `410`, `412`, `415`, `422` — retrying will produce the same result.
Client must fix the request.

For automated clients, optionally include retry guidance in the response:

```json
{
  "type": "https://api.example.com/errors/rate-limited",
  "title": "Rate Limited",
  "status": 429,
  "detail": "Request rate limit exceeded. Try again in 30 seconds.",
  "retry_after": 30
}
```

## Security Rules for Errors

- **Never expose** stack traces, database errors, SQL queries, internal file paths, or server configuration
- **Never expose** which field of a login failed (use generic "invalid credentials" to prevent enumeration)
- **Sanitize** error messages from upstream services before forwarding to clients
- **Log full details server-side** with the `request_id` for debugging; return only safe summaries to clients
- Use the **same error format** for all error responses — inconsistency leaks implementation details

## Consistency Checklist

- [ ] Every endpoint returns errors in the same format
- [ ] Every error includes `type`, `title`, `status`, `detail`
- [ ] Validation errors return all failures, not just the first
- [ ] `request_id` is present in every error response and server logs
- [ ] Rate-limited responses include `Retry-After`
- [ ] No internal details leak in any error response
- [ ] Error `type` URIs are documented and stable

## Further Reading

- [RFC 9457, Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457.html) — current standard for structured error responses (obsoletes RFC 7807)
- [RFC 9110, HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110) — authoritative status code definitions
- [Google AIP-193, Errors](https://google.aip.dev/193)
- [Stripe API Errors](https://docs.stripe.com/api/errors)
- [GraphQL response and errors](https://graphql.org/learn/response/)
