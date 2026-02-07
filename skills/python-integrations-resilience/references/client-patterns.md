# External Integration Client Boundaries

## Outcome

Provider dependencies are isolated behind stable interfaces so domain logic remains portable and testable.

## Boundary Rules

- Wrap each external provider behind an explicit local client interface.
- Keep provider SDKs, auth details, and transport logic in the imperative shell.
- Keep business decisions in the module core; clients only execute side effects.
- Do not expose provider-specific payloads or exceptions to domain callers.

## Contract and Mapping Rules

- Validate request/response payloads at the boundary.
- Map provider errors into local, typed error categories with retryability metadata.
- Preserve cause chains when translating errors (`raise ... from ...`).
- Version boundary DTOs deliberately when provider contracts change.

## Request-Path Guardrails

- Keep request-path orchestration explicit and shallow.
- Avoid service-to-service domain call chains during request handling.
- For cross-module/domain workflows, publish events or enqueue jobs instead of chaining synchronous domain calls.
