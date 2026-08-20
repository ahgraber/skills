---
name: mcp-research
description: |-
  Use when tasks require current, source-backed technical information from MCP tools. Apply for library/API questions, dependency version checks, third-party integration work, framework- or SDK-specific debugging, and any case where stale model knowledge could cause incorrect guidance.
---

# MCP Docs and Research (Context7, Exa, Jina)

## Overview

Use MCP-provided tools to retrieve current, verifiable information instead of relying on memory for fast-changing libraries, APIs, and ecosystem guidance.

## When to Use

- Working with any external library or framework (for example, FastAPI, SQLAlchemy, pandas, boto3, or requests).
- Installing or upgrading dependencies and verifying current versions or migration guidance.
- Implementing features tied to third-party SDKs or APIs.
- Debugging behavior that may be version-specific.
- Looking up current best practices, changelogs, or breaking changes.

## Invocation Notice

- Tell the user when this skill is running: `mcp-research`.
  Skip the notice when the user asked for the skill by name or slash command; spelling and spacing need not match.
  A phrase from this skill's own trigger list is not a name — naming the work is not naming the skill.

## Tool Selection

Inventory the docs and research tools present at runtime and match on capability, not on an exact tool name.
The same server is named differently depending on how it is installed — user scope gives `mcp__jina__read_url`, a plugin-bundled copy gives `mcp__plugin_<plugin>_jina__read_url`, and other harnesses namespace differently again.
If tools are deferred or hidden, discover and load them first.

| Capability need           | What to look for (examples, not an exhaustive list)                                          |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| Library / API docs        | a docs tool with library-id resolution (e.g. Context7 resolve-library-id, then query-docs)   |
| Code-centric examples     | a code-context search tool (e.g. Exa get-code-context) across docs, GitHub, and Q&A sites    |
| Broad current web context | a web-search tool (e.g. Exa web-search, Jina search-web) for announcements and release notes |
| Clean page extraction     | a reader that returns full page text (e.g. Jina read-url)                                    |
| Papers / PDFs             | academic search or PDF extraction (e.g. Jina search-arxiv, extract-pdf)                      |

Use the papers/PDF row only when the task needs paper-level or PDF-structured research.
When none of these is available, fall back to native web search and fetch, and say so in the answer.

## Default Workflow

1. Classify the request: official API docs, implementation examples, or broad web research.
2. Start with the narrowest reliable source:
   - Official docs first (the library/API docs tool) for API correctness.
   - Add code-context and web search only when you need cross-source confirmation or broader context.
3. When the docs tool resolves library ids, resolve the id before querying docs unless the exact id (Context7's `/org/project` form, or the equivalent) is already provided.
4. Keep queries specific (library + feature + version/error) to reduce noisy results.
5. Synthesize findings and clearly separate sourced facts from inferences.

## Quality Rules

- Prefer primary/official documentation for API signatures and behavior.
- For dependency/version decisions, verify with current documentation before recommending versions.
- Avoid unsupported claims; cite concrete tool findings.
- If sources conflict, report the conflict and recommend the safest path (pin version, test in isolation, or check release notes).
- If coverage is weak, state limits explicitly and proceed with best available evidence.
