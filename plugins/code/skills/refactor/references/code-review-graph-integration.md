# Code Review Graph Integration

When the `code-review-graph` MCP plugin is available, use these tools to build and verify a refactor plan.

The graph is more load-bearing here than in a review.
Blast radius is the primary input to the plan, and a plan built on an undercount is a plan the user approved without knowing its size.
Without the graph, establish the same facts by grep: every caller, importer, subclass, and test of what you are about to move.
Say in the plan that the counts came from search rather than the graph.

## Availability Gate

Run once, at Phase 0.

1. Call `build_or_update_graph_tool()` for an incremental update.
2. Call `list_graph_stats_tool()` to verify the graph has nodes and check `last_updated`.
3. If either call fails or the graph is empty → continue on the git-only path.
   Do not retry.

A stale `last_updated` matters more than usual: a plan built from a graph that predates recent commits will miss call sites that now exist.

## Phase 1 — Plan

### Required per move

| Tool                     | Call                                                           | Purpose                                                        |
| ------------------------ | -------------------------------------------------------------- | -------------------------------------------------------------- |
| `get_impact_radius_tool` | `get_impact_radius_tool(changed_files=<targets>, max_depth=2)` | The blast-radius count that goes in the plan. Do not estimate. |
| `query_graph_tool`       | `query_graph_tool(pattern="callers_of", target=<name>)`        | Every call site the move must update.                          |
| `query_graph_tool`       | `query_graph_tool(pattern="tests_for", target=<name>)`         | Which tests are affected, and whether coverage exists at all.  |

A move whose `tests_for` result is empty has no safety net.
Say so in the plan and propose a characterization test as the first step of that move.

### Per move type

| Move                | Tool                                                                | Why                                                           |
| ------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------- |
| Collapse a layer    | `query_graph_tool(pattern="inheritors_of", target=<class>)`         | Confirm the single-implementation precondition                |
| Extract/move module | `query_graph_tool(pattern="importers_of", target=<module>)`         | Every import to update                                        |
| Break a cycle       | `get_architecture_overview_tool()`                                  | Community boundaries and coupling; shows what the cycle spans |
| Rename              | `refactor_tool(mode="rename", old_name=<old>, new_name=<new>)`      | Preview the full reference set before committing to the move  |
| Decompose function  | `find_large_functions_tool(min_lines=50, file_path_pattern=<file>)` | Confirm the target and find peers worth the same treatment    |
| Invert a dependency | `get_affected_flows_tool()`                                         | Which execution paths cross the boundary being changed        |

### Sequencing

Use `get_bridge_nodes_tool` and `get_hub_nodes_tool` when several moves are planned.
Moves touching hub nodes have the widest radius and are the most disruptive to sequence late, so plan them first, while the tree is otherwise untouched.

## Phase 3 — Execute

After each move, before trusting a green suite:

| Tool                  | Call                                                            | Checks                                                            |
| --------------------- | --------------------------------------------------------------- | ----------------------------------------------------------------- |
| `refactor_tool`       | `refactor_tool(mode="dead_code", file_pattern=<touched_files>)` | The move left nothing orphaned behind it                          |
| `query_graph_tool`    | `query_graph_tool(pattern="callers_of", target=<moved_name>)`   | Every caller the plan listed now resolves to the new location     |
| `detect_changes_tool` | `detect_changes_tool(base=<pre-refactor ref>)`                  | The actual change set matches the planned one, with nothing extra |

`detect_changes_tool` is the check against silent scope growth.
If it reports files the plan did not name, stop and re-plan rather than continuing.

Rebuild the graph between moves with `build_or_update_graph_tool()`.
Otherwise the next move's radius is computed against the pre-move tree.

## Tool Quick Reference

All tools accept an optional `repo_root` parameter (auto-detected if omitted).

| Tool                             | Primary use                            | Key parameters                                         |
| -------------------------------- | -------------------------------------- | ------------------------------------------------------ |
| `build_or_update_graph_tool`     | Ensure graph freshness                 | `full_rebuild`, `base`                                 |
| `list_graph_stats_tool`          | Check graph exists and is current      | —                                                      |
| `get_impact_radius_tool`         | Blast-radius counts for the plan       | `base`, `changed_files`, `max_depth`                   |
| `query_graph_tool`               | Relationship queries                   | `pattern`, `target`                                    |
| `get_architecture_overview_tool` | Community boundaries and coupling      | —                                                      |
| `get_affected_flows_tool`        | Execution paths through changed code   | `base`, `changed_files`                                |
| `get_bridge_nodes_tool`          | Nodes joining otherwise separate areas | —                                                      |
| `get_hub_nodes_tool`             | Highest-connectivity nodes             | —                                                      |
| `find_large_functions_tool`      | Decomposition targets                  | `min_lines`, `kind`, `file_path_pattern`               |
| `refactor_tool`                  | Dead code detection, rename preview    | `mode`, `old_name`, `new_name`, `kind`, `file_pattern` |
| `detect_changes_tool`            | Verify actual scope against the plan   | `base`, `changed_files`, `max_depth`                   |
