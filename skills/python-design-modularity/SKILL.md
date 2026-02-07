---
name: python-design-modularity
description: Provides Python design and modularity guidance. Use when changing architecture, module boundaries, readability, or refactor structure.
---

# Python Design and Modularity

## Overview

Use this skill when code design choices affect maintainability, ownership boundaries, or refactor safety.
It emphasizes readability-first design and explicit module contracts.

## Core Rules

- Keep control flow and data movement explicit.
- Keep module ownership and invariants explicit.
- Prefer composition by default.
- Apply Functional Core / Imperative Shell where it improves testability and separation of concerns.
- Separate behavior changes from structural refactors where possible.

## References

- `references/design-rules.md`
- `references/readability-and-complexity.md`
- `references/module-boundaries.md`
- `references/functional-core-shell.md`
- `references/refactor-guidelines.md`
