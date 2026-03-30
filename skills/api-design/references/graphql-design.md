# GraphQL API Design

## Schema Design

### Naming Conventions

| Element                                         | Convention             | Example                                |
| ----------------------------------------------- | ---------------------- | -------------------------------------- |
| Fields and arguments                            | `camelCase`            | `firstName`, `createdAt`               |
| Types (object, input, interface, union, scalar) | `PascalCase`           | `ProductConnection`, `CreateUserInput` |
| Enum values                                     | `SCREAMING_SNAKE_CASE` | `IN_PROGRESS`, `PUBLISHED`             |
| Directives                                      | `camelCase`            | `@deprecated`, `@cacheControl`         |
| Query fields                                    | Noun, no verb prefix   | `products`, not `getProducts`          |
| Mutation fields                                 | Verb-first             | `createUser`, `publishPost`            |

### Type Design Principles

1. **Implement the `Node` interface** on major types with a globally unique `ID` for client caching and refetching
2. **Use custom scalars** for semantically meaningful types: `DateTime`, `URL`, `Email`, `JSON` — not raw `String`
3. **Use enums** for restricted value sets (statuses, categories, sort directions)
4. **Replace foreign key IDs with object references**: `author: User!` instead of `authorId: ID!`
5. **Separate types by context** — use `Viewer`, `UserProfile`, and `TeamMember` instead of a single `User` type when they serve different purposes.
   Repetition is fine when contexts differ.
6. **Group related fields** into intermediate object types when semantically linked
7. **Never mirror database tables** — the schema is a domain model, not a data model

### Nullability

Every field is **nullable by default** in GraphQL.
This is intentional — networked services fail.

**Rules:**

- **Non-null (`!`) is a guarantee.**
  If a non-null field fails to resolve, the error **bubbles up** to the nearest nullable parent, potentially nullifying large sections of the response (the "null blast radius").
- Lists: almost always `[Item!]!` (non-null list of non-null elements)
- Booleans: non-null unless you have legitimate tri-state semantics
- Fields resolved from external services: keep nullable (the service may be down)
- Only mark non-null when you are **certain** the data will always be present
- **Changing non-null to nullable is a breaking change** for clients

## Query Design

### Pagination — Relay Connection Specification

**Always paginate** lists that could grow.
This is both a UX and security requirement (cost-based rate limiting depends on it).

```graphql
type Query {
  products(
    first: Int
    after: String
    last: Int
    before: String
    filter: ProductFilter
    orderBy: ProductOrderBy
  ): ProductConnection!
}

type ProductConnection {
  edges: [ProductEdge!]!
  pageInfo: PageInfo!
  totalCount: Int
}

type ProductEdge {
  cursor: String!
  node: Product!
}

type PageInfo {
  hasNextPage: Boolean!
  hasPreviousPage: Boolean!
  startCursor: String
  endCursor: String
}
```

- Cursors should be **opaque** to clients (base64-encoded)
- Set a **default and server-side max** for `first`/`last` (e.g., default 20, max 100)
- Use **input types** for complex filter objects and **enums** for sort fields/directions

### Filtering and Sorting

```graphql
input ProductFilter {
  category: ProductCategory
  minPrice: Float
  maxPrice: Float
  search: String
}

input ProductOrderBy {
  field: ProductSortField!
  direction: SortDirection!
}

enum ProductSortField {
  CREATED_AT
  PRICE
  NAME
}

enum SortDirection {
  ASC
  DESC
}
```

## Mutation Design

### Five Principles

1. **Specific over generic.**
   `publishPost` and `archivePost` over `updatePost(field, value)`.
   Specific mutations are easier to optimize, validate, and secure.

2. **Single `input` argument.**
   Every mutation takes one argument named `input` of a unique input type:

   ```graphql
   type Mutation {
     createUser(input: CreateUserInput!): CreateUserPayload!
   }

   input CreateUserInput {
     email: String!
     name: String!
     role: UserRole = MEMBER
   }
   ```

3. **Unique payload type.**
   Never return the domain type directly.
   The payload wrapper provides room for metadata, errors, and evolution:

   ```graphql
   type CreateUserPayload {
     user: User
     userErrors: [UserError!]!
   }
   ```

4. **Nest for evolution.**
   Nesting in both input and payload creates room to add/deprecate fields without conflicts.

5. **Name as verb + noun.** `createUser`, `publishPost`, `sendPasswordResetEmail`.

### Error Handling

Use **top-level `errors`** for system/developer errors only (auth failure, rate limit, server error).
Use **typed schema errors** for domain/user-facing errors.

**Recommended pattern — `userErrors` array:**

```graphql
type CreateUserPayload {
  user: User
  userErrors: [UserError!]!
}

type UserError {
  field: [String!]      # Path to the input field that caused the error
  message: String!
  code: UserErrorCode!
}

enum UserErrorCode {
  EMAIL_TAKEN
  INVALID_EMAIL
  NAME_TOO_SHORT
}
```

The `field` path (e.g., `["input", "email"]`) is valuable for form validation UX.

**For public APIs needing more expressiveness**, use union error types with a common interface:

```graphql
interface DisplayableError {
  field: [String!]
  message: String!
}

type EmailTakenError implements DisplayableError {
  field: [String!]
  message: String!
  suggestedEmail: String
}
```

## N+1 Problem and DataLoader

Each resolver runs independently.
A query fetching 10 posts with their authors produces 1 + 10 queries without mitigation.

**DataLoader** solves this via batching and per-request caching:

```python
from aiodataloader import DataLoader


class UserLoader(DataLoader):
    async def batch_load_fn(self, user_ids):
        users = await db.users.find_by_ids(user_ids)
        user_map = {u.id: u for u in users}
        # MUST return in same order as input keys
        return [user_map.get(uid) for uid in user_ids]


# Create per-request (never share across requests)
def get_context(request):
    return {"user_loader": UserLoader()}


# Use in resolver
async def resolve_author(post, info):
    return await info.context["user_loader"].load(post.author_id)
```

**Rules:**

- Create a **new DataLoader instance per request** — never share (data leaks, stale cache)
- Batch function **must return results in the same order** as input keys
- One loader per data access pattern

## Security

### Query Cost and Depth Limiting

GraphQL's flexible queries create a larger attack surface than REST.
Layer defenses:

1. **Trusted documents / persisted queries** (strongest for first-party clients): Client sends a document hash; server only executes known queries
2. **Depth limiting**: Cap nesting depth; apply a stricter limit for nested lists (exponential growth risk)
3. **Breadth limiting**: Limit top-level fields, aliases, and batch operations per request
4. **Query complexity analysis**: Assign cost weights to fields/types; reject queries exceeding a budget.
   Use `@cost` and `@listSize` directives.
5. **Complexity-based rate limiting**: Each client gets a cost budget per time window (not just request count)

### Authentication and Authorization

- **Authentication** happens before GraphQL execution — HTTP middleware validates tokens and attaches user identity to context

- **Authorization** belongs in the **business logic layer**, not in resolvers.
  Resolvers delegate to domain services that encapsulate access rules:

  ```python
  # Business logic — single source of truth
  def get_post_body(viewer, post):
      if post.author_id == viewer.id or viewer.is_admin:
          return post.body
      return None


  # Resolver delegates
  def resolve_body(post, info):
      return get_post_body(info.context["viewer"], post)
  ```

- Use `@auth` directives for declarative field-level access, but the directive implementation should still delegate to the business layer

- Disable introspection in production for non-public APIs

## Schema Evolution

GraphQL avoids traditional versioning.
Instead, evolve continuously:

1. **Add** the new field/type alongside the old one
2. **Deprecate** the old field: `oldField: String @deprecated(reason: "Use newField instead.")`
3. **Monitor** field usage metrics to track which clients still use deprecated fields
4. **Remove** only when usage reaches zero and schema checks confirm no breaking changes

**Safe changes (always non-breaking):** new fields, new types, new enum values, new arguments with defaults.

**Breaking changes (require deprecation workflow):** removing fields, changing types, making nullable fields non-null, removing enum values.

**Principle:** It is easier to add fields than to remove them.
Be conservative about what you expose initially.
