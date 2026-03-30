# API Versioning

## When to Version

Version when you must make a **breaking change**.
Non-breaking changes do not require a new version.

### Breaking changes (require versioning)

- Removing or renaming an endpoint, field, or parameter
- Changing a field's type or format (e.g., string to object, date format change)
- Making an optional parameter required
- Changing response structure (e.g., wrapping in an envelope that wasn't there)
- Changing authentication or authorization requirements
- Altering the semantics of an existing field

### Non-breaking changes (no version needed)

- Adding new endpoints
- Adding new optional fields to responses
- Adding new optional parameters to requests
- Adding new enum values (if clients handle unknown values gracefully)
- Performance improvements with identical contracts
- Bug fixes that align behavior with documented contract

## Versioning Strategies

### URL path versioning (recommended default)

```text
GET /v1/users
GET /v2/users
```

**Pros:** Most visible and discoverable.
Easy to test, cache, and route.
Clear in documentation and logs.
Universally supported by tools.

**Cons:** Creates URI clutter.
May encourage over-versioning.

### Header versioning

```text
GET /users
Accept: application/vnd.myapi+json; version=2
```

or custom header:

```text
GET /users
API-Version: 2
```

**Pros:** Clean URIs.
Decouples versioning from resource identity.

**Cons:** Less discoverable.
Complicates caching (need `Vary` header).
Harder to test in browsers.
Documentation less intuitive.

### Query parameter versioning

```text
GET /users?version=2
```

**Pros:** Easy to switch versions for testing.

**Cons:** Clutters query string.
Can conflict with other parameters.
Less conventional.

### Choosing a strategy

| Consideration       | URL Path           | Header                    | Query Param      |
| ------------------- | ------------------ | ------------------------- | ---------------- |
| Discoverability     | High               | Low                       | Medium           |
| Caching simplicity  | High               | Low (needs `Vary`)        | Medium           |
| URI cleanliness     | Low                | High                      | Medium           |
| Testing ease        | High               | Low                       | High             |
| Content negotiation | No                 | Yes                       | No               |
| **Recommendation**  | **Default choice** | Complex/multi-format APIs | Rarely preferred |

For **most APIs**, use URL path versioning.
Use header versioning only when content negotiation is a real requirement.

For **GraphQL APIs**, do not use any of these.
GraphQL uses continuous evolution with `@deprecated` instead of discrete versions.

## Version Lifecycle

### 1. Introduction

- New version is released alongside the previous version
- Both versions are fully supported and documented
- Migration guide published with the new version

### 2. Deprecation

Signal deprecation via response headers (RFC 8594):

```text
HTTP/1.1 200 OK
Deprecation: true
Sunset: Sat, 01 Mar 2025 00:00:00 GMT
Link: <https://api.example.com/docs/migration/v1-to-v2>; rel="deprecation"
```

- Announce deprecation **at least 6 months** before sunset
- Include the `Sunset` header with the retirement date
- Log which clients still use deprecated versions
- Proactively notify consumers (email, dashboard, developer portal)

### 3. Sunset

- Return `410 Gone` with a migration link for a 30-day grace period
- After grace period, remove the version entirely
- Keep documentation archived for reference

### Recommended timeline

| Phase                                           | Duration                  |
| ----------------------------------------------- | ------------------------- |
| Both versions active and supported              | 6-12 months               |
| Deprecation announced (headers + notifications) | Start of overlap period   |
| Old version returns `Sunset` headers            | Throughout overlap        |
| Old version returns `410 Gone`                  | 30 days after sunset date |
| Old version fully removed                       | After grace period        |

## Best Practices

1. **Maintain at most 2-3 active versions.**
   More than that creates unsustainable maintenance burden.
2. **Version the contract, not the implementation.**
   Rewriting Node.js in Rust with no API change should not create a new version.
3. **Design for extensibility to minimize versioning.**
   Use objects over primitives, optional fields over required, enums with unknown-value handling.
4. **Document the versioning policy** in your API terms of service: what constitutes a breaking change, warning periods, migration timelines.
5. **Include version in every response** (header or body) so clients can verify they're hitting the expected version.
6. **Never version individual endpoints differently.**
   All endpoints in a version should share the same lifecycle.
7. **Semantic versioning for APIs** — major version in URL (v1, v2), minor/patch in changelog only.
   Clients care about breaking changes, not internal patch numbers.

## Anti-Patterns

| Anti-Pattern                                          | Problem                           |
| ----------------------------------------------------- | --------------------------------- |
| Breaking changes without version bump                 | Silently breaks clients           |
| Too many active versions (4+)                         | Unsustainable maintenance         |
| Short deprecation periods (< 3 months)                | Alienates consumers               |
| Versioning individual endpoints inconsistently        | Confusing, hard to document       |
| Date-based versioning without clear major breakpoints | Hard to know which changes matter |
| No sunset plan                                        | Versions accumulate forever       |
