---
name: simplify
description: |-
  Use when cutting slop out of working code: duplication, dead code, needless indirection, comment noise, defensive padding. Scope is whatever you point it at: current changes (default), a file, a directory, or the repo. Triggers: 'simplify this', 'clean this up', 'de-slop this code', 'strip the cruft', 'tighten this diff', 'this code is bloated'. Not for judging correctness or merge readiness (use code-review), and not for structural change that needs a plan and approval (use refactor).
---

# Simplify: Remove Slop from Working Code

## Invocation Notice

- Inform the user when this skill is being invoked by name: `simplify`.

## Overview

Simplify assumes the code is correct and asks whether it is as simple as it could be.
It exists because models drift additively: left alone, agent-written code accumulates verbosity and structural padding that prompting alone does not prevent.
This skill is the recurring corrective pass.

It edits directly, preserves behavior exactly, and verifies each edit before making the next.
Scope is configurable: the default is the current change set, but a file, a directory, or the whole repo are equally valid targets when the user names one.

Every pass ends with a report persisted to a dated file (see `references/edit-ledger.md`).
The file matters most for deletions, because a diff shows what was removed but cannot carry why removing it was safe.

Anything a configured linter or formatter already flags is out of scope.
Run the tool instead, and review only what those tools cannot check.

## When to Use

- Code is written, tests pass, and it needs cleaning before anyone reads it.
- A change works but feels padded: wrappers on wrappers, checks that cannot fire, flags with one caller.
- A feature was deleted, and the code that only served it needs to go too.
- The comments in a change are noise and need auditing.

## When Not to Use

- Judging code belongs to `code-review`: correctness, edge cases, security, test adequacy, merge readiness.
- Structural change that needs a plan belongs to `refactor`: decomposing a large function, splitting a module, breaking an import cycle.
- If the tests are red, fix them first.
- Simplify never adds capability.
  New behavior is a different task.

## What Goes Elsewhere

When a lens agent surfaces one of these, record it in the ledger and tell the user.
Do not act on it here.

| Finding                                              | Belongs to                              |
| ---------------------------------------------------- | --------------------------------------- |
| Wrong behavior, broken contract, unhandled edge case | `code-review`                           |
| Missing or incorrect error handling                  | `code-review`                           |
| Security exposure                                    | `code-review` (via `securing-code`)     |
| Tests absent, inadequate, or asserting internals     | `code-review`                           |
| Concurrency defects, leaks, hot-path cost            | `code-review`                           |
| Docs or specs describing behavior that changed       | ledger suggestion; user decides         |
| Function decomposition, module split, layering fix   | ledger Deferred; `refactor` can execute |

Excess belongs to simplify; absence belongs to code-review.
For example, error handling that catches and re-raises unchanged is a simplify finding, and missing error handling is a code-review finding.

## Edit Tiers

Classify every finding before applying anything.

**Tier 1 — apply directly — is any edit whose behavior preservation you can verify right now**, at the current rung of the verification ladder, within the stated scope.
Deleting dead code, collapsing a forwarding wrapper, flattening nesting with a guard clause, fixing a stale comment, unifying duplicated logic: all Tier 1 when the verification passes afterward.

**Tier 2 — record as a proposal, never apply** — is everything you cannot verify now, plus these regardless of verifiability:

- It changes an exported signature or public API, including deleting an export.
- It requires editing an existing test's assertions to pass.
- It conflicts with a spec.
- It removes something that still has a consumer.

Tier 2 items go to the ledger's Deferred section with a proposed move, a blast-radius estimate, and a verification plan.
They are proposals for the user; the `refactor` skill knows how to execute a Deferred list, but nothing obligates that path.

If an edit needs a test's assertions changed to pass, the behavior changed.
Revert it and record it as Tier 2.
Fixing a stale comment or a typo inside a test file is an ordinary Tier 1 edit; the rule guards assertions, not file paths.

## Verification Ladder

A Tier 1 edit is safe only when verification can confirm it.
Establish the strongest available rung before editing, and use it for every edit:

1. **Full test suite** with the relevant code exercised.
2. **Typecheck plus lint**, when no suite exists or it does not cover the target.
3. **Characterization test** written before a risky edit to pin current behavior; it stays afterward.
4. **Parse and import smoke checks**, when the repo has no checks at all.
5. **Report-only.**
   If nothing above is available for the target, do not edit it; record the finding instead.

Record the rung in the ledger header.
If a check fails after an edit and the failure looks unrelated, re-run once before attributing it to the edit.
For a risky deletion whose safety rests on a covering test, confirm the test actually guards it: break the invariant deliberately and check the test fails.

## Removal Rule

Agent-written code accumulates unused parts, so removal is the default.
For a candidate with no consumer and no live reason, remove it unless you can name a reason to keep it.

Ask two questions of every removal candidate:

1. **Who consumes this?**
   A caller, a test that asserts its behavior, a spec clause, a documented public entry point, a runtime hook.
   Static search is not sufficient to answer "nobody": also sweep text — string-keyed dispatch, config keys, entry-point declarations, fixtures, templates, serialized data, environment examples.
   Code registered by string does not appear in the import graph, so a static search misses it.
2. **If nothing consumes it, does history reveal a reason that still applies?**
   Read blame, the introducing commit, and adjacent comments.
   A platform quirk that is still shipped, a workaround for a bug still open: keep, and record the reason.
   A shim whose other side is gone: the reason expired; remove.

If both questions come up empty, remove the code and record both answers in the ledger.
If either is answered, keep it and record the answer.

Boundary cases:

- **Compatibility with unshipped code is not protected.**
  A shim or interface that only ever existed within the current unshipped work is not a consumer; delete it on sight.
  If a piece of code only makes sense to someone who watched this session happen, it is overfitted.
- **Deleting any exported symbol is a public API change**: Tier 2, whatever the consumer search says.
- **A guard needs evidence.**
  Absence of failure and absence of the hazard look identical from the outside.
  If you cannot show the hazard is impossible, keep the guard and record the doubt.

**Report the direction of travel.**
State what was removed and what was added, and if the pass grew the surface area, say why.
Never delete to move a number; line count is a report, not a target.

## Phase 0 — Gate

### 1. Baseline

Find the repo's checks and establish the highest verification-ladder rung available.
Run it before any edit.
If the suite exists and is red, stop and report; without a green start, no later failure is attributable.
Record the rung, the command, and the result for the ledger header.

### 2. Scope

Take the scope the user named: a file, a directory, the repo, or a change set.
When the scope is the current changes (the default), run `scripts/build_review_packet.py` to resolve it deterministically and pre-bake one packet — diff plus changed-file list — that the lens agents read by path.
Fall back to `git diff` or `git diff HEAD` for a manual change set; with no git changes and no named scope, use the files edited earlier in this conversation.
For a file, directory, or repo scope, the file list is the packet; note that broad scopes deserve narrow lens selection or the pass sprawls.

### 3. Specs

Look for a spec source: an `openspec/` or `specs/` tree, or artifacts from the `sdd` family.
When one exists, every edit must leave the code compliant with it.
Suggested spec revisions go in the ledger, and this skill never applies them.

### 4. Graph tooling

If the `code-review-graph` MCP plugin is available, call `build_or_update_graph_tool(base=<base>)`, then `list_graph_stats_tool()` to confirm the graph has nodes.
If either call fails or the graph is empty, continue on the git-only path and do not retry.
When the graph is available, follow `references/code-review-graph-integration.md` at each later phase.

### 5. Lens selection

The lenses are independent, and a user often wants only one.

| ID  | Lens                   | Covers                                                                                                     | Reference                            |
| --- | ---------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| L1  | Duplication & reuse    | Code that re-implements something the codebase already has; near-duplicate blocks                          | —                                    |
| L2  | Obfuscative complexity | Indirection without abstraction, premature generalization, action at a distance, defensive noise, ceremony | `references/obfuscation-patterns.md` |
| L3  | Removal                | Dead code, orphans, shims whose other side is gone, branches on now-constant flags                         | Removal Rule above                   |
| L4  | Comments               | Narration, restatement, staleness, point-in-time rot                                                       | `references/comment-audit.md`        |
| L5  | Semantic naming        | Misleading names, one concept under several names, semantically duplicated constants                       | —                                    |

L5 covers only what a linter cannot: a `get*` that mutates, the same value named three ways across layers, the same constant defined twice with different spellings.
Stylistic naming and formatting stay with the linter.

If the user's request already names a concern, run the matching lenses and say which you selected.
Otherwise ask which to run, offering all five as the default.
Do not fan out five agents on a request the user meant narrowly.

## Phase 1 — Triage

Read the scope to understand what the code is doing and why.
Intent matters: code that looks over-built can be implementing a requirement the diff does not show.

When the graph is available, see `references/code-review-graph-integration.md` Phase 1:

- `detect_changes_tool(base=<base>)` for risk-scored, priority-ordered triage (change-set scopes).
- `get_review_context_tool(base=<base>)` for structural context without reading whole files.
- Optionally `get_affected_flows_tool` (2+ files) or `get_architecture_overview_tool` (3+ directories).

## Phase 2 — Lens Agents

Dispatch one agent per selected lens, all in a single message.

Give each agent the packet path (or file list), its lens reference, the Edit Tiers rules, and the Removal Rule.
Tell each agent the scope is a floor and not a ceiling: L1's search for existing utilities is inherently outside it, and L3 must check consumers across the whole repo.

**Agents report; they do not edit.**
Parallel edits conflict, and verification has to run against one coherent state.

Each finding comes back with the file and line, the lens, what to change, why, and a tier with the reason for that tier.
An agent that cannot justify Tier 1 assigns Tier 2.

Graph tools per lens, when available:

- L1 uses `semantic_search_nodes_tool` for existing equivalents, and `query_graph_tool("callers_of")`.
- L2 uses `get_impact_radius_tool` before collapsing a layer, and `find_large_functions_tool`.
- L3 uses `refactor_tool(mode="dead_code")`, plus `query_graph_tool("callers_of")` and `query_graph_tool("tests_for")` for the static half of the consumer question.
  The textual sweep and the history question remain manual.
- L5 uses `query_graph_tool("importers_of")` before touching anything exported.

## Phase 3 — Apply and Verify

1. Aggregate findings and drop duplicates across lenses.
2. Re-check every Tier 1 classification yourself.
   An agent that wants its finding applied has an incentive to under-report blast radius.
3. Apply Tier 1 edits **one at a time**: make the edit, run the verification rung, then move on.
   A failure attributes itself to the edit that caused it.
4. On failure, revert that edit and reclassify it as Tier 2 with the failure recorded.
   Do not weaken an assertion, relax a type, or skip a test to get to green.
5. Write the ledger per `references/edit-ledger.md`.

Group trivially independent edits (comment deletions across files) into one verification step when running checks per edit would be absurd; the unit of revert is then the group.

Skip a false-positive finding and record it in the ledger's Skipped section.
Do not argue with it.

**Rationale goes in the ledger, not the code.**
Do not leave a comment explaining what you removed or why you changed something.
The reader has the ledger next to the diff, and a comment narrating this pass is accurate for one commit and misleading afterward.

## Phase 4 — Report

Tell the user, briefly:

- What was applied, grouped by lens
- What was removed, and the net line movement
- What is in Deferred, and the ledger path
- The verification rung, with baseline and final results

Deferred items are proposals: the user decides what happens to them, and `refactor` is one way to execute the structural ones.
Do not start that work here.

## References

- `references/edit-ledger.md` — the persisted report: location, sections, and the deletion-proof format.
- `references/obfuscation-patterns.md` — L2 pattern catalog with the disconfirming test for each.
- `references/comment-audit.md` — L4 keep/delete/fix criteria and the docstring boundary.
- `references/code-review-graph-integration.md` — tool dispatch playbook for the `code-review-graph` MCP plugin.
