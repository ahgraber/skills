# Pydantic at Boundaries

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Use Pydantic For

- Request/response schemas.
- Event/message payload validation.
- External system data ingress.
- Typed environment settings (`pydantic-settings`).

## Prefer Plain Types For

- Internal pure transformations.
- Tight inner loops where framework validation adds no value.
- Domain logic that already operates on validated value objects.

## Modeling and Validation Rules

- Validate untrusted inputs at ingress with explicit models or `TypeAdapter`.
- When the project is on Pydantic v2, prefer these APIs in new code:
  - `BaseModel.model_validate(...)`
  - `BaseModel.model_validate_json(...)`
  - `model_dump(...)` / `model_dump_json(...)` at egress
- Use strict validation for untrusted boundary data when coercion would hide bugs.
- Keep `BaseModel` types out of pure core logic unless the model is itself the domain value object.
- Translate `ValidationError` at module boundaries into domain/application errors with added context.

## Boundary Pattern

1. Validate untrusted data at ingress.
2. Convert into domain-friendly structures.
3. Keep domain behavior independent of transport/schema concerns.
4. Re-encode at egress with explicit output schemas.
