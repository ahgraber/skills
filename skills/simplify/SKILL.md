---
name: simplify
description: Review changed code for reuse, quality, and efficiency, then fix any issues found.
---

# Simplify: Code Review and Cleanup

Review all changed files for reuse, quality, and efficiency.
Fix any issues found.

## Phase 0: Gate — Scope & Tools

Determine what changed and what tooling is available before any analysis.

### Scope detection

Run `git diff` (or `git diff HEAD` if there are staged changes) to see what changed.
If there are no git changes, review the most recently modified files that the user mentioned or that you edited earlier in this conversation.

### Graph-enhanced tooling gate

If the `code-review-graph` MCP plugin is available, probe and ensure freshness:

1. Call `build_or_update_graph_tool(base=<base>)` to run an incremental update.
2. Call `list_graph_stats_tool()` to verify the graph has nodes and check `last_updated`.
3. If either call fails or the graph is empty → proceed with the git-only path for the remainder of the review.
   Do not retry.

When the graph is available, follow `references/code-review-graph-integration.md` for enhanced analysis at each subsequent step.

## Phase 1: Triage

**Always (git-based):**

- Review the diff to understand what changed and why.

**When graph is available** (see `references/code-review-graph-integration.md` Phase 1):

- Run `detect_changes_tool(base=<base>)` for risk-scored, priority-ordered triage.
- Run `get_review_context_tool(base=<base>)` for token-efficient structural context.
- Optionally run `get_affected_flows_tool` (2+ files) or `get_architecture_overview_tool` (3+ directories).

Pass all available context — diff, and graph triage data if available — to each agent in Phase 2.

## Phase 2: Launch Three Review Agents in Parallel

Use the Agent tool to launch all three agents concurrently in a single message.
Pass each agent the diff (and graph context from Phase 1 if available).
When graph data includes risk scores, instruct agents to review highest-risk items first.

### Agent 1: Code Reuse Review

For each change:

1. **Search for existing utilities and helpers** that could replace newly written code.
   Look for similar patterns elsewhere in the codebase — common locations are utility directories, shared modules, and files adjacent to the changed ones.
   When graph is available: use `semantic_search_nodes_tool` and `query_graph_tool("callers_of")` per the integration reference.
2. **Flag any new function that duplicates existing functionality.**
   Suggest the existing function to use instead.
3. **Flag any inline logic that could use an existing utility** — hand-rolled string manipulation, manual path handling, custom environment checks, ad-hoc type guards, and similar patterns are common candidates.
4. **Orphaned code**: when functions were deleted or replaced, verify nothing was left unreferenced.
   When graph is available: use `refactor_tool(mode="dead_code")` per the integration reference.

### Agent 2: Code Quality Review

Review the same changes for hacky patterns:

1. **Redundant state**: state that duplicates existing state, cached values that could be derived, observers/effects that could be direct calls
2. **Parameter sprawl**: adding new parameters to a function instead of generalizing or restructuring existing ones
3. **Copy-paste with slight variation**: near-duplicate code blocks that should be unified with a shared abstraction
4. **Leaky abstractions**: exposing internal details that should be encapsulated, or breaking existing abstraction boundaries.
   When graph is available: use `get_impact_radius_tool` per the integration reference.
5. **Stringly-typed code**: using raw strings where constants, enums (string unions), or branded types already exist in the codebase
6. **Oversized functions**: functions that have grown beyond reasonable length.
   When graph is available: use `find_large_functions_tool` per the integration reference.
7. **Broken contracts**: changed function signatures, return types, or behavioral contracts that leave callers out of sync.
   Grep for callers in the codebase and verify they still match.
   When graph is available: use `query_graph_tool("callers_of")` and `query_graph_tool("inheritors_of")` per the integration reference.
8. **Test coverage gaps**: behavior changes without corresponding test updates.
   Search for test files that exercise the changed functions.
   When graph is available: use `query_graph_tool("tests_for")` per the integration reference.
9. **Unnecessary comments**: comments explaining WHAT the code does (well-named identifiers already do that), narrating the change, or referencing the task/caller — delete; keep only non-obvious WHY (hidden constraints, subtle invariants, workarounds)

### Agent 3: Efficiency Review

Review the same changes for efficiency:

1. **Unnecessary work**: redundant computations, repeated file reads, duplicate network/API calls, N+1 patterns.
   When graph is available: use `query_graph_tool("callees_of")` per the integration reference.
2. **Missed concurrency**: independent operations run sequentially when they could run in parallel
3. **Hot-path bloat**: new blocking work added to startup or per-request/per-render hot paths.
   When graph is available: cross-reference with affected flows from Phase 1.
4. **Recurring no-op updates**: state/store updates inside polling loops, intervals, or event handlers that fire unconditionally — add a change-detection guard so downstream consumers aren't notified when nothing changed.
   Also: if a wrapper function takes an updater/reducer callback, verify it honors same-reference returns (or whatever the "no change" signal is) — otherwise callers' early-return no-ops are silently defeated
5. **Unnecessary existence checks**: pre-checking file/resource existence before operating (TOCTOU anti-pattern) — operate directly and handle the error
6. **Memory**: unbounded data structures, missing cleanup, event listener leaks
7. **Overly broad operations**: reading entire files when only a portion is needed, loading all items when filtering for one.
   When graph is available: use `query_graph_tool("importers_of")` per the integration reference.

## Phase 3: Fix Issues

Wait for all three agents to complete.
Aggregate their findings and fix each issue directly.
If a finding is a false positive or not worth addressing, note it and move on — do not argue with the finding, just skip it.

When done, briefly summarize what was fixed (or confirm the code was already clean).

## References

- `references/code-review-graph-integration.md` — tool dispatch playbook for `code-review-graph` MCP plugin (availability gate, required + optional tools per phase, tool quick reference).
