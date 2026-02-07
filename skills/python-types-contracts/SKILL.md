---
name: python-types-contracts
description: Provides Python typing and contract guidance. Use when defining or evolving public interfaces, schema boundaries, or pydantic usage.
---

# Python Types and Contracts

## Scope Note

- Treat these recommendations as preferred defaults for common cases, not universal rules.
- If a default conflicts with project constraints or worsens the outcome, suggest a better-fit alternative and explain why it is better for this case.
- When deviating, call out tradeoffs and compensating controls (tests, observability, migration, rollback).

## Invocation Notice

- Inform the user when this skill is being invoked by name: `python-types-contracts`.

## Overview

Use this skill for interface-level design in Python code.
Focus on explicit contracts, stable public APIs, and boundary-safe modeling.

## Core Rules

- Treat type hints as interface design, not decoration.
- Type public APIs and keep contracts explicit.
- Prefer narrow interfaces and boundary protocols.
- Use pydantic at trust boundaries by default, not everywhere.
- Make compatibility and migration impact explicit for contract changes.

## References

- `references/typing-policy.md`
- `references/contract-evolution.md`
- `references/pydantic-boundaries.md`
