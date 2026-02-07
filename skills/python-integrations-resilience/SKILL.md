---
name: python-integrations-resilience
description: Provides Python external integration guidance. Use when designing client boundaries, outbound reliability policy, or resilience/contract testing for providers.
---

# Python Integrations and Resilience

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Invocation Notice

- Inform the user when this skill is being invoked by name: `python-integrations-resilience`.

## Overview

Use this skill for external API/provider work where reliability and contract behavior must be explicit and testable.

## Core Rules

- Hide provider-specific details behind explicit client boundaries.
- Keep domain logic isolated from provider SDK specifics.
- Require explicit timeout/retry/idempotency policy for outbound operations.
- Test both contract mapping and failure behavior directly.

## References

- `references/client-patterns.md`
- `references/request-reliability-policy.md`
- `references/resilience-and-contract-testing.md`
