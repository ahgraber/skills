# URI Design

## Core Principles

1. **URIs are for people first.**
   They should be readable, speakable, and predictable.
   Can you say it out loud and have it make sense?
2. **URIs are permanent.**
   Once published, a URI's meaning should not change.
   Use HTTP 301 redirects when restructuring.
3. **URIs identify resources, not actions.**
   The resource is the noun; the HTTP method is the verb.

## Naming Rules

### Use plural nouns for collections

```text
GET /users                ✓
GET /user                 ✗

GET /products             ✓
GET /product              ✗
```

### Use lowercase with hyphens

RFC 3986 does not require lowercase or hyphens — these are conventions, not URI syntax rules.
Consistency within an API matters more than any one naming style.
That said, lowercase with hyphens is the dominant convention and avoids case-sensitivity surprises across servers and clients.

```text
/user-profiles            ✓ hyphens for multi-word segments (preferred)
/user_profiles            ~ underscores (acceptable if consistent; some tools truncate under links)
/userProfiles             ~ camelCase (uncommon; avoid for public APIs)
/UserProfiles             ✗ PascalCase (avoid)
```

### Use descriptive slugs, not database IDs

Where resources have natural names, use human-readable slugs over raw database IDs.
This is a strong preference for public APIs; internal APIs may use opaque IDs where slugs add no value.

```text
/products/ballpoint-pen   ✓ human-readable slug
/products/23              ~ opaque database ID (acceptable for internal APIs)
```

For APIs where resources don't have natural slugs, UUIDs are preferred over sequential integers — they don't leak ordering or volume information.

### No file extensions or technology markers

```text
/users/123                ✓
/users/123.json           ✗
/api.php/users            ✗
/cgi-bin/get_users        ✗
```

### No trailing slashes

Trailing slashes are not forbidden by URI syntax, but including them creates ambiguity and inconsistency.
The strong convention is to omit them; redirect to the canonical form if received.

```text
/users                    ✓ canonical form
/users/                   ~ redirect to /users with 301 if received; don't treat as a separate resource
```

## Path Structure

### Common format

```text
/{resource}/{identifier}/{sub-resource}?{modifiers}
```

**Examples:**

```text
/users
/users/abc-123
/users/abc-123/orders
/users/abc-123/orders/ord-456
/products?category=electronics&sort=-price&page=2
```

If the API versions in the path, prepend the version segment consistently rather than treating it as part of the resource hierarchy.

### Path segments = hierarchy; query params = modifiers

Path segments represent the **resource hierarchy** (identity, containment).
Query parameters represent **non-hierarchical modifiers** (filtering, sorting, pagination, field selection).

```text
/users/123/orders?status=active&sort=-created_at    ✓
/users/123/orders/active/sort/created_at            ✗
```

### Limit nesting to 2 levels

```text
/users/{id}/orders                    ✓ 1 level of nesting
/users/{id}/orders/{id}               ✓ 2 levels
/users/{id}/orders/{id}/items/{id}    ✗ too deep — flatten or use links
```

Beyond 2 levels, either promote the sub-resource to a top-level resource or return URIs in response bodies.

## Query Parameter Conventions

| Purpose                     | Convention                                | Example                     |
| --------------------------- | ----------------------------------------- | --------------------------- |
| Filtering                   | Field name = value                        | `?status=active&role=admin` |
| Sorting                     | `sort` with +/- prefix or field direction | `?sort=-created_at,+name`   |
| Pagination                  | `page` + `per_page` or `cursor`           | `?page=2&per_page=20`       |
| Field selection             | `fields` (comma-separated)                | `?fields=id,name,email`     |
| Search                      | `q` or `search`                           | `?q=john`                   |
| Including related resources | `include` or `expand`                     | `?include=author,comments`  |

## Actions That Don't Map to CRUD

Some operations don't fit neatly into resource CRUD.
The REST API Design Rulebook calls these **controller resources** — a recognized archetype alongside documents, collections, and stores.

For the full decision tree, when-to-use guidance, and examples, see [rest-design.md § Resource Archetypes](rest-design.md).

In brief, prefer in this order:

1. **State transition** — `PATCH /orders/{id}` with `{"status": "cancelled"}`
2. **Sub-resource** — `POST /orders/{id}/cancellation`
3. **Controller** — `POST /orders/{id}/cancel` (verb as the last URI segment, no children)

Controllers are a pragmatic escape hatch, not a loophole.
If you find yourself reaching for them frequently, reconsider whether your resource model is too fine-grained.

## Hackability

Well-designed URIs are **hackable** — users can navigate by modifying them:

```text
/events/2024/03         → March 2024 events
/events/2024            → All 2024 events (should work)
/events                 → All events (should work)
```

If a URI segment is removable, the truncated URI should return a meaningful response (the parent collection or a summary).

## Further Reading

- Mark Massé, _REST API Design Rulebook_ (O'Reilly, 2011) — four resource archetypes and URI naming rules per archetype
- [RFC 3986, URI Generic Syntax](https://www.rfc-editor.org/rfc/rfc3986)
- [Microsoft REST API URL guidance](https://github.com/microsoft/api-guidelines/blob/vNext/azure/Guidelines.md#uniform-resource-locators-urls)
- [Google AIP-122, Resource names](https://google.aip.dev/122)
- [Google AIP-136, Custom methods](https://google.aip.dev/136) — Google's approach to non-CRUD operations
- [Zalando URL guidelines](https://opensource.zalando.com/restful-api-guidelines/#135)
