---
name: code-review
description: |-
  Use when reviewing code changes before committing or merging — staged diffs, branch diffs, or PR readiness checks. Triggers: 'review my code', 'check these changes', 'review this branch', 'give feedback on my diff', 'is this PR ready?'. Not for implementing features, running test suites, or formatting-only passes.
---

# Code Review

## Invocation Notice

- Inform the user when this skill is being invoked by name: `code-review`.

## Overview

Structured, actionable code review focused on correctness, bugs, style, and maintainability.
Act as a senior engineer: thorough, pragmatic, impact-first.

## Constraints

- Do NOT modify code unless explicitly asked.
- Do NOT guess missing code or behavior; ask for missing context.
- Do NOT suggest adding suppressions (e.g., `#pragma warning disable`).
- Stay focused on review quality; avoid unrelated commentary.
- Work strictly from the provided diff or code context.

## When to Use

- Reviewing staged changes before committing.
- Reviewing branch changes before merging or opening a PR.
- Checking a diff for correctness, bugs, style, or structure.
- Final review of all changes on a feature branch.
- Quick sanity-check of a small changeset before pushing.

**When NOT to use:**

- Implementing new features from scratch.
- Running test suites (see `python-testing` or equivalent).
- Refactoring without a prior review (review first, then refactor on request).
- Linting or formatting only — use a linter or formatter directly.

## Quick Reference

| Area                        | Look for                                                                                                                     |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Correctness & Logic         | Wrong behavior, broken contracts, off-by-one                                                                                 |
| Bugs & Edge Cases           | Nil/null paths, boundary values, error propagation                                                                           |
| Code Quality & Style        | Naming, readability, idiomatic usage                                                                                         |
| Structure & Maintainability | Coupling, duplication, separation of concerns                                                                                |
| Best Practices              | Language/framework conventions, SOLID, DRY                                                                                   |
| Test Adequacy               | Missing tests for behavior changes, regression gaps                                                                          |
| Performance                 | N+1 queries, unbounded loops/fan-out, missing pagination, sync calls in hot paths, large allocations, missed async           |
| Security & Risk             | OWASP Top 10: access control, injection, crypto, auth, supply chain, logging, error handling — use `securing-code` checklist |
| Documentation               | Misleading comments, missing doc for public API                                                                              |

## Common Mistakes

- **Reviewing without full context** — jumping to conclusions without reading the complete diff or understanding intent.
- **Mixing review and edits** — modifying code during the review phase instead of separating feedback from implementation.
- **Nitpick overload** — burying critical issues under dozens of style nitpicks.
- **Ignoring intent** — critiquing design choices without understanding the constraints or goals behind them.
- **Incomplete scope** — reviewing only one file when the change spans multiple files or modules.

## Workflow

### Step 0 — Gate: Scope & Tools

Determine review scope and available tooling before doing any analysis.

**Scope detection:**

Identify whether this is a pre-commit or pre-merge review, then set the `base` ref accordingly.

_Pre-commit (staged changes):_

```sh
# List staged files
git diff --cached --name-status

# View staged diff
git --no-pager diff --cached
```

_Pre-merge (branch vs. target):_

```sh
# Resolve target base branch from origin/HEAD when available
BASE_BRANCH=$(git rev-parse --abbrev-ref origin/HEAD 2>/dev/null)
BASE_BRANCH=${BASE_BRANCH#origin/}
BASE_BRANCH=${BASE_BRANCH:-main}
MERGE_BASE=$(git merge-base "$BASE_BRANCH" HEAD)

# List changed files on this branch relative to the target base
git diff --name-status "$MERGE_BASE"...HEAD

# View full branch diff
git --no-pager diff "$MERGE_BASE"...HEAD
```

If the user does not specify scope, infer from context:

- On a feature branch with commits ahead of the target base branch → pre-merge review.
- Staged changes present → pre-commit review.
- Ask if ambiguous, especially when default branch detection fails.

**Graph-enhanced tooling gate:**

If the `code-review-graph` MCP plugin is available, probe and ensure freshness:

1. Call `build_or_update_graph_tool()` to run an incremental update.
2. Call `list_graph_stats_tool()` to verify the graph has nodes and check `last_updated`.
3. If either call fails or the graph is empty → proceed with the git-only path for the remainder of the review.
   Do not retry.

When the graph is available, follow `references/code-review-graph-integration.md` for enhanced analysis at each subsequent step.
The reference doc specifies required and optional tool calls per phase, with decision criteria for when to use each.

**Parallel subagent gate:**

If the `Agent` tool is available and the change is non-trivial, plan to use the parallel-subagent path in Step 2.
See `references/parallel-subagent-review.md` for the thresholds, dispatch pattern, and prompt templates.
Otherwise continue with the single-agent path.

### Step 1 — Triage & Context

Build a prioritized review plan before reading any code in detail.

**Always (git-based):**

- Review the diff to understand what changed and why.
- For medium/large or cross-module changes, write a short review plan focused on risk hotspots.

**Git diagnostics** (useful for unfamiliar codebases or large diffs — see `references/git-diagnostics-before-review.md`):

1. Check file churn and bug clusters to identify which changed files historically attract the most defects.
2. Review team composition and recent contributor activity for bus-factor context.
3. Look for firefighting patterns (reverts, hotfixes) that signal stability risks in the areas under review.

**When graph is available** (see `references/code-review-graph-integration.md` Phase 1):

- Call `detect_changes_tool(base=<base>)` for risk-scored, priority-ordered triage.
  Use its risk scores to order files highest-risk first.
- Call `get_review_context_tool(base=<base>)` for token-efficient structural context instead of reading entire changed files.
- Optionally call `get_affected_flows_tool` (change touches 2+ files), `get_architecture_overview_tool` (change spans 3+ directories), or `get_impact_radius_tool` (need raw blast-radius data) as the scope warrants.

**Triage output:** Produce a prioritized file list and a brief review plan identifying the highest-risk areas to focus on.

### Step 2 — Structured Review (No Edits)

Pick the path set at the Step 0 parallel subagent gate.

**Parallel-subagent path** (when gate is active):

Follow `references/parallel-subagent-review.md` — fan out quality, spec-compliance, and security subagents in parallel (plus architecture when warranted), synthesize, dispatch a devil's-advocate subagent for a challenge pass, then do final synthesis and tiebreak yourself.
The security subagent (Agent 4) is always dispatched; it uses the OWASP Top 10:2025 checklist from `securing-code` skill references.
Include the architecture subagent when: pre-merge / pre-PR review, the user mentions "merge", the user explicitly requests architectural review, or you judge it necessary (confirm with the user before dispatching).
Clarify author intent with the user before dispatching; subagents have no conversation history.
Skip the single-agent steps below — the reference doc drives this path end-to-end through Step 3.

**Single-agent path** (default):

For each changed file or module, summarize what changed and why.
Review tests before implementation: do tests exist for the changed behavior, do they assert behavior (not internals), do they cover edge cases and regressions?
Test gaps shape what to scrutinize in the implementation pass.
Then evaluate each area in the Quick Reference table above.

Rules:

- If intent is unclear, ask clarifying questions before judging.
- If an area has no issues, state that explicitly.
- Reference specific code locations (line numbers or quoted snippets).
- Keep feedback actionable and concise.
- Review all changed lines before final judgment; open surrounding context where needed.
- Address runtime errors, validation, error handling, concurrency risks, resource usage, and obvious performance pitfalls.
- Behavior changes without tests → raise an issue (at least Medium).
- Style comments are non-blocking unless they map to project conventions.
- Dependency manifest or lockfile changes → assess supply-chain risk and compatibility.
- Call out TODO comments and their implications.
- For security & risk: use `securing-code` skill's `references/tier2-review.md` checklist (OWASP-mapped) as the evaluation framework.

**When graph is available** (see `references/code-review-graph-integration.md` Phase 2):

- For every changed function: call `query_graph_tool(pattern="tests_for", target=<function>)` to flag test coverage gaps.
- For interface/signature changes: call `query_graph_tool(pattern="callers_of", target=<function>)` to verify consumers are updated.
- Optionally use `query_graph_tool("importers_of")` for module-level API changes, `query_graph_tool("inheritors_of")` for base class changes, `find_large_functions_tool` for complexity flags, `semantic_search_nodes_tool` to check for duplication, and `refactor_tool("dead_code")` to catch orphaned code.

Compile findings into issues using the template in `assets/issue-template.md`.
Sort issues by priority: critical > high > medium > low.
For each issue, include blocking status, confidence, and evidence.

### Step 3 — Report

Present the review as a prioritized list of issues from Step 2.

**When graph was used**, append:

- **Blast Radius Summary** — directly changed functions/files, impacted downstream count, affected execution flows.
- **Test Coverage Gaps** — table of changed functions with no test coverage or insufficient coverage for new behavior.

### Step 4 — Apply Changes (Only on Explicit Request)

Proceed only when the user asks to "apply changes", "fix issues", "implement suggestions", or similar.

1. Apply only changes discussed in Step 2.
2. Make minimal, targeted edits.
3. Do not introduce additional refactors without user approval.
4. After editing, summarize what changed and why, mapping back to the original review items.

## Scope Note

Treat these recommendations as preferred defaults.
When a default conflicts with project constraints, suggest a better-fit alternative, call out tradeoffs, and note compensating controls.

## References

- `assets/issue-template.md` — issue type/priority legends and suggestion format.
- `references/review-best-practices-links.md` — external review best-practice links used by this skill.
- `references/git-diagnostics-before-review.md` — git commands for assessing codebase health before reviewing.
- `references/code-review-graph-integration.md` — tool dispatch playbook for `code-review-graph` MCP plugin (required + optional tools per phase, decision guide).
- `references/parallel-subagent-review.md` — parallel-subagent dispatch path: thresholds, agent prompt templates, synthesis and red-team steps.
- `securing-code` skill (`references/tier2-review.md`, `references/tier3-*.md`) — OWASP-mapped security checklist used by the security subagent and single-agent security lens.
