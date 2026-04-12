# Code Review Graph Integration

When the `code-review-graph` MCP plugin is available, use these tools to enhance each review phase.
This reference is a **hybrid playbook**: required tools that always fire, plus optional tools with decision criteria.

## Availability Gate

Run this check once at the start of every review before entering the main workflow.

1. Call `build_or_update_graph_tool()` (incremental update, uses `base` ref from scope detection).
2. Call `list_graph_stats_tool()` to verify the graph has nodes and check `last_updated`.
3. If either call fails or the graph is empty → set `graph_available = false` and proceed with the git-only workflow.
   Do not retry.

The `base` ref follows review scope:

| Scope                       | `base` value                    |
| --------------------------- | ------------------------------- |
| Pre-commit (staged changes) | `HEAD` (staged vs working tree) |
| Pre-merge (branch diff)     | Target branch, e.g. `main`      |
| Specific commits            | The parent commit ref           |

## Phase 1 — Triage & Context

### Required

| Tool                      | Call                                   | Purpose                                                                                                                                                                             |
| ------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `detect_changes_tool`     | `detect_changes_tool(base=<base>)`     | Risk-scored, priority-ordered list of changed functions with review guidance. This replaces manual diff scanning for triage.                                                        |
| `get_review_context_tool` | `get_review_context_tool(base=<base>)` | Token-efficient structural context: changed files, impacted nodes, source snippets, test coverage gaps, and inheritance concerns. Use this instead of reading entire changed files. |

### Optional

| Tool                             | Use when                                                                                                                     | Call                                               |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| `get_affected_flows_tool`        | Change touches 2+ files or modifies a function that could be on a critical path                                              | `get_affected_flows_tool(base=<base>)`             |
| `get_impact_radius_tool`         | You need the raw blast-radius data beyond what `detect_changes_tool` already provides (e.g., to report impacted file counts) | `get_impact_radius_tool(base=<base>, max_depth=2)` |
| `get_architecture_overview_tool` | Change spans 3+ files across different directories/modules                                                                   | `get_architecture_overview_tool()`                 |
| `list_communities_tool`          | You need to understand module boundaries before reviewing a cross-cutting change                                             | `list_communities_tool(sort_by="size")`            |

### Triage output

Use the results from `detect_changes_tool` to:

- Order files by risk score (highest first).
- Focus the review plan on files the graph flags as high-impact (many dependents, no test coverage).
- Skip files the graph marks as low-risk isolated changes (leaf nodes with tests).

## Phase 2 — Structured Review

### Required (per changed function/file)

| Tool                            | Call                                                            | Purpose                                                                                                          |
| ------------------------------- | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `query_graph_tool("tests_for")` | `query_graph_tool(pattern="tests_for", target=<function_name>)` | Flag changed functions that lack test coverage. Behavior changes without tests → at least Medium priority issue. |

### Required (for interface/signature changes)

| Tool                             | Call                                                             | Purpose                                                                                                 |
| -------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `query_graph_tool("callers_of")` | `query_graph_tool(pattern="callers_of", target=<function_name>)` | Verify that callers are updated when a function signature, return type, or behavioral contract changes. |
| `query_graph_tool("callees_of")` | `query_graph_tool(pattern="callees_of", target=<function_name>)` | Check downstream dependencies when a function's internal behavior changes.                              |

### Optional

| Tool                                | Use when                                                                                                       | Call                                                                        |
| ----------------------------------- | -------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| `query_graph_tool("importers_of")`  | A module-level export or public API changes                                                                    | `query_graph_tool(pattern="importers_of", target=<file_or_module>)`         |
| `query_graph_tool("inheritors_of")` | A base class or interface changes                                                                              | `query_graph_tool(pattern="inheritors_of", target=<class_name>)`            |
| `query_graph_tool("file_summary")`  | You need to understand the full structure of a file without reading it                                         | `query_graph_tool(pattern="file_summary", target=<file_path>)`              |
| `find_large_functions_tool`         | Reviewing files with significant additions; flag functions that grew past complexity thresholds                | `find_large_functions_tool(min_lines=50, file_path_pattern=<changed_file>)` |
| `semantic_search_nodes_tool`        | A new function or class is added and you want to check for existing similar implementations (duplication risk) | `semantic_search_nodes_tool(query=<function_name_or_description>)`          |
| `refactor_tool("dead_code")`        | Functions were deleted or replaced; verify nothing was left orphaned                                           | `refactor_tool(mode="dead_code", file_pattern=<changed_file>)`              |

## Phase 3 — Report Enrichment

When CRG was used, append these sections to the standard review output:

### Blast Radius Summary

```text
### Blast Radius
- **Directly changed**: X functions across Y files
- **Impacted downstream**: N functions, M files (depth 2)
- **Affected flows**: [list critical execution paths touched]
```

### Test Coverage Gaps

```text
### Test Coverage Gaps
| Function | File | Status |
|---|---|---|
| `function_name` | `path/to/file.ext` | No tests found |
| `other_function` | `path/to/other.ext` | Tests exist but don't cover new behavior |
```

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
| `list_communities_tool`          | Module structure overview            | `sort_by`, `min_size`                                           |
| `query_graph_tool`               | Relationship queries                 | `pattern`, `target`                                             |
| `find_large_functions_tool`      | Complexity flags                     | `min_lines`, `kind`, `file_path_pattern`                        |
| `semantic_search_nodes_tool`     | Find similar/related code            | `query`, `kind`, `limit`                                        |
| `refactor_tool`                  | Dead code detection, rename preview  | `mode`, `old_name`, `new_name`, `kind`, `file_pattern`          |
