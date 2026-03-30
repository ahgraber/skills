# REST vs GraphQL: Decision Framework

## Quick Decision Tree

```text
Is your primary concern...

Multiple clients with different data needs? ──→ GraphQL
  (mobile needs 3 fields, web needs 20)

Simple CRUD on well-defined resources? ──→ REST
  (users, products, orders)

Aggregating data from multiple backends? ──→ GraphQL
  (single gateway, multiple services)

Strong HTTP caching requirements? ──→ REST
  (CDN, browser cache, proxy cache)

Deeply nested, interconnected data? ──→ GraphQL
  (social graphs, content with relations)

Real-time subscriptions needed? ──→ GraphQL
  (live updates, notifications)

File upload/download is primary? ──→ REST
  (binary data, streaming)

Need both? ──→ Hybrid
  (REST for resources + caching, GraphQL for aggregation)
```

## When Each Excels

### Choose REST when

- **Simple CRUD** on well-defined, independent resources (users, products, invoices)
- **All clients consume data uniformly** — no significant difference in data needs across platforms
- **HTTP caching is critical** — REST's multi-endpoint model maps naturally to cache keys (CDN, browser, proxy)
- **File upload/download** is a primary concern — REST handles binary data natively
- **Simpler operational model** — monitoring, rate limiting, error handling, and debugging are more straightforward with discrete endpoints
- **Team has limited GraphQL experience** — REST's learning curve is lower
- **Public APIs with broad adoption** — REST is universally understood; more third-party tooling exists

### Choose GraphQL when

- **Multiple client types** (web, mobile, IoT) with **different data needs** — mobile needs 3 fields, web needs 20
- **Over-fetching or under-fetching** is a persistent problem — clients make multiple REST calls to assemble one view
- **Deeply nested, interconnected data** — social graphs, content management, e-commerce catalogs
- **Aggregating multiple backend services** behind a single endpoint — GraphQL as a gateway/BFF
- **Frontend team needs autonomy** — request exactly the data they need without backend endpoint changes
- **Real-time capabilities** — subscriptions are built into the GraphQL spec
- **Bandwidth-constrained clients** — mobile on cellular; minimize payload sizes
- **Rapidly evolving frontend** — new views and features without new endpoints

### Hybrid approach

REST and GraphQL are **not mutually exclusive**.
Many production systems use both:

- REST for simple, cacheable resource endpoints and file handling
- GraphQL for complex, multi-source data aggregation and flexible queries
- A shared auth and rate-limiting layer across both

## Tradeoff Matrix

| Dimension            | REST                              | GraphQL                                                                                           |
| -------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Endpoints**        | Multiple, resource-oriented       | Single endpoint                                                                                   |
| **Data shape**       | Fixed response per endpoint       | Client-specified per query                                                                        |
| **Type safety**      | Optional (OpenAPI adds it)        | Built-in schema + type system                                                                     |
| **Caching**          | Native HTTP caching               | Requires custom strategies (persisted queries, CDN with GET)                                      |
| **Error handling**   | HTTP status codes (4xx, 5xx)      | HTTP status codes for transport/protocol errors; execution errors may return `data` plus `errors` |
| **Versioning**       | URL/header versioning             | Continuous evolution via `@deprecated`                                                            |
| **File handling**    | Native multipart upload           | Requires workarounds (multipart spec or separate REST endpoint)                                   |
| **Real-time**        | Requires SSE/WebSocket separately | Subscriptions built-in                                                                            |
| **Discoverability**  | OpenAPI/Swagger docs              | Introspection + schema docs                                                                       |
| **Learning curve**   | Lower                             | Higher                                                                                            |
| **Tooling maturity** | Very mature                       | Mature and growing rapidly                                                                        |
| **N+1 risk**         | Controlled by endpoint design     | Inherent; mitigated by DataLoader                                                                 |
| **Security surface** | Smaller (fixed queries)           | Larger (arbitrary queries require depth/cost limiting)                                            |

## Design-First vs Code-First

This decision is orthogonal to REST vs GraphQL but affects both:

### Design-first (recommended for non-trivial APIs)

Write the contract (OpenAPI spec or GraphQL schema) before implementation code.

**Benefits:**

- Early feedback from stakeholders before investment in code
- Parallel development — frontend, backend, and QA work from the same contract
- API design is not constrained by implementation choices
- Auto-generate server stubs, client SDKs, and mock servers

**Best for:** Externally consumed APIs, multi-team projects, APIs with governance requirements.

### Code-first (acceptable for prototypes and internal tools)

Implement the server, generate the spec from code annotations/decorators.

**Benefits:**

- Faster initial development
- Single source of truth (the code)
- Lower ceremony for small teams

**Risks:**

- Generated specs can drift from actual behavior
- API design influenced by implementation convenience
- Harder for non-developers to review the contract

**Mitigation:** If using code-first, generate and version-control the spec on every build.
Run automated checks to detect spec drift.

## Migration Considerations

### REST to GraphQL

- Start by wrapping existing REST endpoints behind GraphQL resolvers (REST as data source)
- Use DataLoader to batch REST calls and avoid N+1
- Migrate incrementally — one domain/resource at a time
- Keep the REST API running during transition; deprecate endpoints as GraphQL coverage grows

### GraphQL to REST

- Unusual but sometimes necessary (simplifying, reducing operational complexity)
- Map each commonly-used query to a dedicated REST endpoint
- Lose client flexibility but gain caching and operational simplicity

## Further Reading

- [GraphQL.org Thinking in Graphs](https://graphql.org/learn/thinking-in-graphs/)
- [GraphQL.org Best Practices](https://graphql.org/learn/best-practices/)
- [Microsoft REST API design guidance](https://learn.microsoft.com/en-us/azure/architecture/best-practices/api-design)
- [Google API Design Guide](https://docs.cloud.google.com/apis/design)
- [Apollo, Demand-oriented schema design](https://www.apollographql.com/docs/graphos/schema-design/guides/demand-oriented-schema-design)
