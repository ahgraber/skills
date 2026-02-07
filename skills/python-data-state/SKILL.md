---
name: python-data-state
description: Provides Python data and state boundary guidance. Use when modeling ownership, consistency boundaries, data lifecycle, or configuration strategy.
---

# Python Data and State

## Overview

Use this skill when changes touch data ownership, validation boundaries, consistency models, or runtime configuration behavior.

## Core Rules

- Make module ownership and invariants explicit.
- Validate at ingress and normalize before domain decisions.
- Share minimal data across boundaries.
- Avoid cross-module transactions by default.
- Keep configuration typed, environment-driven, and startup-validated.

## References

- `references/data-lifecycle.md`
- `references/consistency-boundaries.md`
- `references/configuration.md`
