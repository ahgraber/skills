# Code Review Graph Integration

When the `code-review-graph` MCP plugin is available, use these tools to enhance each simplify phase.
This reference is a **hybrid playbook**: the availability gate runs once, then each phase has graph-enhanced steps that layer on top of the git-only workflow.

## Availability Gate

Run this check once at the start before entering the main workflow.

1. Call `build_or_update_graph_tool(base=<base>)` to run an incremental update.
2. Call `list_graph_stats_tool()` to verify the graph has nodes and check `last_updated`.
3. If either call fails or the graph is empty → proceed with the git-only path for the remainder of the review.
   Do not retry.

The `base` ref follows review scope:

| Scope          | `base` value                    |
| -------------- | ------------------------------- |
| Staged changes | `HEAD` (staged vs working tree) |
| Branch diff    | Target branch, e.g. `main`      |

## Phase 1 — Triage

### Required

| Tool                      | Call                                   | Purpose                                                                                                  |
| ------------------------- | -------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| `detect_changes_tool`     | `detect_changes_tool(base=<base>)`     | Risk-scored, priority-ordered list of changed functions. Use risk scores to order review items.          |
| `get_review_context_tool` | `get_review_context_tool(base=<base>)` | Token-efficient structural context: changed files, impacted nodes, source snippets, test gaps, warnings. |

### Optional

| Tool                             | Use when                                             | Call                                               |
| -------------------------------- | ---------------------------------------------------- | -------------------------------------------------- |
| `get_affected_flows_tool`        | Change touches 2+ files or a potential critical path | `get_affected_flows_tool(base=<base>)`             |
| `get_architecture_overview_tool` | Change spans 3+ directories/modules                  | `get_architecture_overview_tool()`                 |
| `get_impact_radius_tool`         | Need raw blast-radius data beyond detect_changes     | `get_impact_radius_tool(base=<base>, max_depth=2)` |

## Phase 2 — Lens Enhancements

Lens IDs match the table in `SKILL.md`.
Only lenses selected at the Phase 0 gate run.

### L1: Duplication & reuse

| Tool                         | Use when                                                   | Call                                                               |
| ---------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------ |
| `semantic_search_nodes_tool` | New function/class added — check for existing similar code | `semantic_search_nodes_tool(query=<function_name_or_description>)` |
| `query_graph_tool`           | Confirm a utility is an established reuse pattern          | `query_graph_tool(pattern="callers_of", target=<utility_name>)`    |

### L2: Obfuscative complexity

| Tool                        | Use when                                                                   | Call                                                                        |
| --------------------------- | -------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `get_impact_radius_tool`    | Before collapsing a layer — wide radius means the collapse is Tier 2       | `get_impact_radius_tool(base=<base>, max_depth=2)`                          |
| `query_graph_tool`          | Trace forwarding chains — a callee chain that only forwards is indirection | `query_graph_tool(pattern="callees_of", target=<function_name>)`            |
| `find_large_functions_tool` | Size flag; decomposition itself is Tier 2, so record rather than apply     | `find_large_functions_tool(min_lines=50, file_path_pattern=<changed_file>)` |
| `query_graph_tool`          | Single-implementation check before collapsing an interface                 | `query_graph_tool(pattern="inheritors_of", target=<class_name>)`            |

### L3: Removal

The graph answers only the static half of the consumer question.

| Tool               | Use when                                        | Call                                                           |
| ------------------ | ----------------------------------------------- | -------------------------------------------------------------- |
| `refactor_tool`    | Find orphans after a deletion or replacement    | `refactor_tool(mode="dead_code", file_pattern=<changed_file>)` |
| `query_graph_tool` | Consumer question — is anything calling this?   | `query_graph_tool(pattern="callers_of", target=<name>)`        |
| `query_graph_tool` | Consumer question — does a test assert on this? | `query_graph_tool(pattern="tests_for", target=<name>)`         |
| `query_graph_tool` | Consumer question — is this imported anywhere?  | `query_graph_tool(pattern="importers_of", target=<module>)`    |

Empty results on all three do **not** close the question.
The graph is static structure; it cannot see string-keyed dispatch, entry-point declarations, config-registered classes, fixtures, templates, or serialized references.
The Removal Rule's textual sweep is still required, and the history question still needs `git blame` and the introducing commit.

### L4: Comments

No graph tools apply.
Use `query_graph_tool(pattern="tests_for", target=<function>)` when a comment documents a gotcha, to check whether a test covers it before recording the gap.

### L5: Naming & constants

| Tool               | Use when                                                | Call                                                                |
| ------------------ | ------------------------------------------------------- | ------------------------------------------------------------------- |
| `query_graph_tool` | Before renaming anything exported — count the importers | `query_graph_tool(pattern="importers_of", target=<file_or_module>)` |
| `refactor_tool`    | Preview a rename's full reference set                   | `refactor_tool(mode="rename", old_name=<old>, new_name=<new>)`      |

## Tool Quick Reference

All tools accept an optional `repo_root` parameter (auto-detected if omitted).

| Tool                             | Primary use                          | Key parameters                                                  |
| -------------------------------- | ------------------------------------ | --------------------------------------------------------------- |
| `build_or_update_graph_tool`     | Ensure graph freshness               | `full_rebuild`, `base`                                          |
| `list_graph_stats_tool`          | Check graph exists and is current    | —                                                               |
| `detect_changes_tool`            | Risk-scored change triage            | `base`, `changed_files`, `include_source`, `max_depth`          |
| `get_review_context_tool`        | Token-efficient review context       | `base`, `changed_files`, `include_source`, `max_lines_per_file` |
| `get_impact_radius_tool`         | Raw blast-radius data                | `base`, `changed_files`, `max_depth`                            |
| `get_affected_flows_tool`        | Execution paths through changed code | `base`, `changed_files`                                         |
| `get_architecture_overview_tool` | Community boundaries and coupling    | —                                                               |
| `query_graph_tool`               | Relationship queries                 | `pattern`, `target`                                             |
| `find_large_functions_tool`      | Complexity flags                     | `min_lines`, `kind`, `file_path_pattern`                        |
| `semantic_search_nodes_tool`     | Find similar/related code            | `query`, `kind`, `limit`                                        |
| `refactor_tool`                  | Dead code detection, rename preview  | `mode`, `old_name`, `new_name`, `kind`, `file_pattern`          |
