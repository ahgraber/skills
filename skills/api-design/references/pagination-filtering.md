# Pagination and Filtering

## Pagination Strategies

### Strategy comparison

| Strategy        | Performance at Scale | Random Access | Consistency                   | Complexity | Best For                               |
| --------------- | -------------------- | ------------- | ----------------------------- | ---------- | -------------------------------------- |
| **Offset/Page** | Degrades             | Yes           | May skip/duplicate on changes | Low        | Small datasets, admin UIs              |
| **Cursor**      | Stable               | No            | Consistent                    | Medium     | Large datasets, feeds, infinite scroll |
| **Keyset**      | Stable               | No            | Consistent                    | Medium     | Time-series, sorted data               |

### Offset/page-based pagination

```text
GET /users?page=3&per_page=20
```

Response includes metadata:

```json
{
  "data": [...],
  "meta": {
    "page": 3,
    "per_page": 20,
    "total": 245,
    "total_pages": 13
  }
}
```

**Pros:** Simple to implement.
Supports random page access.
Users can bookmark/share specific pages.

**Cons:** Performance degrades with large offsets (`OFFSET 100000` scans rows).
Records can be skipped or duplicated when data changes between requests.

**Use when:** Datasets are small-to-medium, users need random page access (admin tables, dashboards).

### Cursor-based pagination

```text
GET /users?first=20&after=eyJpZCI6MTIzfQ==
```

Response:

```json
{
  "data": [...],
  "meta": {
    "has_next_page": true,
    "has_previous_page": true,
    "next_cursor": "eyJpZCI6MTQzfQ==",
    "previous_cursor": "eyJpZCI6MTI0fQ=="
  }
}
```

Cursors are **opaque** to clients (typically base64-encoded).
The server decodes them to determine the query position.

**Pros:** Stable performance regardless of position.
No skipped/duplicated records.
Works with real-time data.

**Cons:** No random page access.
Cannot show "page 3 of 13".
Cannot jump to arbitrary positions.

**Use when:** Large datasets, infinite scroll, feeds, real-time data, mobile apps.

### Keyset pagination

A variant of cursor-based that uses the last seen value of the sort key:

```text
GET /events?after_date=2024-03-15T10:00:00Z&limit=20
```

More transparent than opaque cursors but exposes sort implementation.
Suitable when the sort key is meaningful to clients (timestamps, alphabetical order).

## Defaults and Limits

| Parameter                        | Recommended Default | Recommended Max |
| -------------------------------- | ------------------- | --------------- |
| Page size (`per_page` / `first`) | 20                  | 100             |
| Minimum                          | 1                   | —               |

- **Always enforce a server-side maximum** even if the client requests more
- **Document** default and max values in the API spec
- Optionally support `?include_total=true` for total count (expensive on large tables — make it opt-in)

## Filtering

### Query parameter conventions

```text
GET /products?category=electronics&status=active&min_price=10&max_price=100
```

| Pattern         | Example                                                          | Use                 |
| --------------- | ---------------------------------------------------------------- | ------------------- |
| Exact match     | `?status=active`                                                 | Single value filter |
| Multiple values | `?status=active,pending` or `?status[]=active&status[]=pending`  | OR filter           |
| Range           | `?min_price=10&max_price=100` or `?price[gte]=10&price[lte]=100` | Numeric/date ranges |
| Search          | `?q=wireless+keyboard` or `?search=wireless+keyboard`            | Full-text search    |
| Existence       | `?has_avatar=true`                                               | Boolean filter      |
| Negation        | `?status[not]=deleted` or `?exclude_status=deleted`              | Exclude values      |

Pick a consistent convention and document it.
Don't mix styles within one API.

### Nested field filtering

For filtering on related resource fields:

```text
GET /orders?customer.tier=premium
```

or use bracket notation:

```text
GET /orders?filter[customer.tier]=premium
```

## Sorting

### Convention

```text
GET /products?sort=-created_at,+name
```

- `+` prefix (or no prefix) = ascending
- `-` prefix = descending
- Comma-separated for multi-field sort
- Alternative: `?sort=created_at&order=desc` (simpler but limits to single field)

### Rules

- **Document sortable fields** — not all fields should be sortable (only indexed ones)
- **Define a default sort** for every collection endpoint (typically `-created_at`)
- **Invalid sort fields** should return `400 Bad Request`, not silently ignore

## Field Selection (Sparse Fieldsets)

Allow clients to request only the fields they need:

```text
GET /users?fields=id,name,email
```

- Reduces payload size (especially valuable for mobile clients)
- For nested resources: `?fields=id,name,orders.id,orders.total`
- Return `400` for invalid field names
- Always include `id` regardless of field selection

## Combining Pagination, Filtering, and Sorting

All three compose via query parameters:

```text
GET /products?category=electronics&min_price=50&sort=-rating&page=2&per_page=10&fields=id,name,price,rating
```

**Important:** Filtering and sorting should be applied **before** pagination.
The pagination window operates on the filtered, sorted result set.

## Link Headers (RFC 5988)

Optionally include pagination links in response headers:

```text
Link: <https://api.example.com/users?page=3&per_page=20>; rel="next",
      <https://api.example.com/users?page=1&per_page=20>; rel="prev",
      <https://api.example.com/users?page=13&per_page=20>; rel="last",
      <https://api.example.com/users?page=1&per_page=20>; rel="first"
```

This follows the GitHub API pattern and keeps links machine-readable without polluting the response body.

## Edge Cases

| Scenario                     | Response                                                                     |
| ---------------------------- | ---------------------------------------------------------------------------- |
| Empty result set             | `200 OK` with empty `data` array, pagination meta showing 0 total            |
| Page beyond last page        | `200 OK` with empty `data` array (not 404)                                   |
| Negative page number         | `400 Bad Request`                                                            |
| `per_page` exceeding max     | Silently cap to max, or return `400` (document which approach you use)       |
| Invalid cursor               | `400 Bad Request` with descriptive error                                     |
| Filtering returns no results | `200 OK` with empty array (not 404 — the collection exists, it's just empty) |

## Further Reading

- [GraphQL.org Pagination](https://graphql.org/learn/pagination/)
- [Google AIP-158, Pagination](https://google.aip.dev/158)
- [Google AIP-160, Filtering](https://google.aip.dev/160)
- [Stripe Pagination](https://docs.stripe.com/api/pagination)
- [Zalando pagination guidelines](https://opensource.zalando.com/restful-api-guidelines/#pagination)
