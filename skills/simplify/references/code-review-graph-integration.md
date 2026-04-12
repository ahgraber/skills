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

## Phase 2 — Agent Enhancements

### Agent 1: Code Reuse

| Tool                         | Use when                                                   | Call                                                               |
| ---------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------ |
| `semantic_search_nodes_tool` | New function/class added — check for existing similar code | `semantic_search_nodes_tool(query=<function_name_or_description>)` |
| `query_graph_tool`           | Confirm a utility is an established reuse pattern          | `query_graph_tool(pattern="callers_of", target=<utility_name>)`    |
| `refactor_tool`              | Functions deleted or replaced — check for orphaned code    | `refactor_tool(mode="dead_code", file_pattern=<changed_file>)`     |

### Agent 2: Code Quality

| Tool                        | Use when                                                        | Call                                                                        |
| --------------------------- | --------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `get_impact_radius_tool`    | Verify abstraction boundaries — wide blast radius = likely leak | `get_impact_radius_tool(base=<base>, max_depth=2)`                          |
| `find_large_functions_tool` | Flag functions that grew past complexity thresholds             | `find_large_functions_tool(min_lines=50, file_path_pattern=<changed_file>)` |
| `query_graph_tool`          | Signature/contract changes — verify callers are updated         | `query_graph_tool(pattern="callers_of", target=<function_name>)`            |
| `query_graph_tool`          | Base class changes — check subclass compatibility               | `query_graph_tool(pattern="inheritors_of", target=<class_name>)`            |
| `query_graph_tool`          | Test coverage gaps — flag changed functions without tests       | `query_graph_tool(pattern="tests_for", target=<function_name>)`             |

### Agent 3: Efficiency

| Tool               | Use when                                                              | Call                                                                |
| ------------------ | --------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `query_graph_tool` | Trace downstream call chains to spot redundant/overlapping work       | `query_graph_tool(pattern="callees_of", target=<function_name>)`    |
| `query_graph_tool` | Check consumer breadth — broad imports amplify inefficiency costs     | `query_graph_tool(pattern="importers_of", target=<file_or_module>)` |
| Affected flows     | Cross-reference Phase 1 flow data — high-criticality = extra scrutiny | Use `get_affected_flows_tool` results from Phase 1                  |

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
