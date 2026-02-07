---
name: python-notebooks-async
description: Provides Python notebook async guidance. Use when writing or reviewing asyncio code in .ipynb or '#%%' notebook workflows with host-owned event loops.
---

# Python Notebooks Async

## Overview

Use this skill when Python async code runs inside notebooks or mixed notebook/script workflows.
It focuses on event-loop ownership, orchestration patterns, and compatibility constraints.

## Core Rules

- Treat notebook kernels as loop-owned environments.
- Prefer top-level `await` and explicit task orchestration.
- Avoid `asyncio.run()` inside notebook cells.
- Keep reusable async logic in regular modules.
- Use `nest_asyncio` only as a constrained compatibility fallback.

## References

- `references/notebooks-async.md`
