# Discovery Phase

Discovery is a phase, not a single subagent.
The orchestrator makes two sequential calls:

1. **`discovery-explore`** — fan out parallel explorer subagents, each running a methodologically distinct technique.
   Each emits structured findings.
2. **`discovery-synthesize`** — single synthesizer subagent consumes all explorer outputs, reconciles agreements and disagreements, produces a capability menu with overlaps, external-surface candidates, and gotchas.

The orchestrator then presents the menu to the user for Pre-flight Consent (SKILL.md Phase 3).

## Why parallel explorers + synthesizer

Each explorer is methodologically distinct (graph algorithm, AST traversal, data-flow analysis, framework recognition, schema parsing, test-suite analysis).
Different techniques surface different signals:

- Call graph alone misses state coupling (shared DB writes, shared topics)
- AST alone misses runtime DI registration
- Schema artifacts alone miss undocumented behavior

Parallel fan-out gives each technique its own context budget for its own job.
The synthesizer's role is reconciliation, not exploration — its prompt is specifically about "where do these signals agree, disagree, and what gotchas should the user know about?"

This is **not** greenfield-style fan-out (many roles wearing one analyzer skill).
The discriminator is methodological distinctness: each explorer has a different _technique_, not just a different label.

## Explorer set

Default explorer set (extensible):

| Explorer          | Technique                                                                                | When to run                                         |
| ----------------- | ---------------------------------------------------------------------------------------- | --------------------------------------------------- |
| `call-graph`      | `code-review-graph` (preferred) or naive AST traversal                                   | Always (graph if available, AST fallback)           |
| `data-flow`       | String-literal scanning for table names, queue names, topic names, file paths, env keys  | Always                                              |
| `port-interface`  | Framework-aware extraction of interface declarations, DI registrations, route decorators | Always (framework heuristics applied conditionally) |
| `schema-artifact` | Detect and parse OpenAPI, GraphQL, Protobuf, SQL schemas                                 | Conditional on artifact presence                    |
| `test-suite`      | Identify test files, link to capability scope via filename and import patterns           | Conditional on test directory presence              |

Each explorer reports `status: ran | not_applicable | failed` with a one-line `status_reason` when not run.

## Per-explorer guidance

Each explorer has a methodologically distinct procedure.
The orchestrator dispatches each subagent with the appropriate procedure embedded in its prompt.

### `call-graph` explorer

Preferred technique: `code-review-graph` (a CLI tool building a structural AST graph with communities, bridges, hubs, impact radius).
Fallback: naive AST traversal across the codebase.

**With `code-review-graph` available:**

1. Build or update the graph: `code-review-graph build`
2. Query communities, hub nodes, and bridges in the codebase region matching the user's intent
3. For each candidate capability, query impact radius from its entry points to detect blast into other regions
4. Use graph findings to drive `references` in findings — hub objects, community member files, bridge nodes
5. Skip files the graph shows are unrelated to any candidate capability

**Without `code-review-graph` (AST fallback):**

1. Walk imports and call edges from likely entry points (`main`, route handlers, CLI entry points, test fixtures)
2. Cluster files by import locality + filename heuristics (directory structure, naming conventions)
3. Mark `confidence: medium` or `low` for capability candidates derived from heuristics alone
4. Surface a `gotcha` if the codebase has language coverage gaps the AST walker can't span

The fallback explorer's findings are strictly less rich than the graph version; the synthesizer weights them accordingly.

### `data-flow` explorer

Scans for cross-capability state coupling that the call graph misses.

1. Extract string literals matching: SQL table/column references, queue/topic names, file paths, env var keys, cache key patterns, config file paths
2. Group by literal — sites that share a literal across capability candidates are _synthetic bridges_ (state-coupling overlaps)
3. Emit `kind: overlap` findings for each synthetic bridge with `kind: state` (distinguishing from call-graph `kind: call` overlaps)
4. Emit `kind: external_surface_candidate` for literals matching known external system patterns (e.g., HTTP hosts, third-party DB schemas)

This explorer is the primary defense against the "call graph misses shared writes to the same DB row" failure mode.

### `port-interface` explorer

Framework-aware extraction of interface declarations and registrations.

1. Detect framework patterns (Spring `@Module`/`@Component`, NestJS controllers/providers, FastAPI route decorators, Rails controllers, Django views, gRPC service definitions)
2. Extract declared interfaces, ports, and DI bindings
3. Emit `kind: capability_candidate` based on interface boundaries — these may agree or disagree with call-graph communities
4. Emit `kind: external_surface_candidate` for declared public APIs (HTTP routes, gRPC methods, CLI commands, library exports)
5. Apply framework heuristics conditionally — skip steps that don't match detected frameworks

When call-graph and port-interface explorers disagree about capability boundaries, the synthesizer surfaces this as an `axis_disagreement` rather than picking one.

### `schema-artifact` explorer

Detects schema artifacts and runs the snapshot lifecycle.
This explorer is the canonical home for schema discovery.

**Step 1: Detect schema artifacts.**
Look for:

- Committed specs: `openapi.yaml`, `swagger.json`, `openapi.json`, `docs/api/`, `openapi/`
- Schema files: `.proto`, `.graphql`, `.prisma`, `.avsc`, `schema.sql`, migrations directories
- Framework markers implying runtime schema generation: FastAPI, NestJS, Spring Boot, DRF, Rails API, Go Echo/Gin, Laravel, GraphQL servers, gRPC

If no schema artifacts are detected, report `status: not_applicable` with a one-line reason.

**Step 2: Check for `.specs/.sdd/schema-config.yaml`.**

- If present: use the configured extraction commands.
- If absent and schema artifacts were detected: report this in findings as a `kind: anomaly` so the orchestrator can prompt the user to create one (one-time suggestion, see SKILL.md).
  Do not block on this; proceed with detection-only findings.

See `sdd-schema.md` for the config file format.

**Step 3: Generate snapshots (when extraction is configured).**
Run the configured commands and store output in `.specs/schemas/`.
This produces a generated schema snapshot reflecting the runtime/code state.

**Step 4: Diff authored vs generated.**
If the repo contains both a committed authored schema (e.g., `docs/openapi.yaml`) and a generated snapshot, diff them:

- Paths in authored but not generated → **aspirational** (planned but not yet implemented)
- Paths in generated but not authored → **undocumented drift**
- Type or shape mismatches → **potential bugs or stale spec**

Emit findings:

- Aspirational paths → `kind: capability_candidate` with `confidence: low` and signal `aspirational_only` (the lifter may handle these as ADDED-only delta candidates)
- Undocumented drift → `kind: anomaly` with signal `undocumented_drift`
- Mismatches → `kind: anomaly` with signal `schema_mismatch`

**Step 5: Surface schema-anchored findings.**
For each schema path that maps to a capability candidate, include the schema path in the finding's `signals` (e.g., `signals: [schema_path:/users/{id}]`).
The lifter uses these to add `**Schema reference:**` annotations to relevant scenarios — see `lifter.md`.

### `test-suite` explorer

Identifies test files and links them to capability candidates.

1. Detect test directories (`tests/`, `__tests__/`, `*_test.go`, `*.spec.ts`, etc.)
2. Match test files to capability candidates via filename, import patterns, and fixtures
3. Emit findings as `kind: capability_candidate` evidence — test files appear in `references` with `relationship: test`, strengthening capability proposals
4. Tests that assert on specific behaviors (assertions, expected outputs) are higher-weight evidence than tests that only exercise the code path

This explorer corroborates other explorers' findings; it rarely emits standalone capability candidates.

## Explorer output schema

Each explorer's output is a report with metadata + a flat list of findings.
A finding is one cohesive observation the explorer wants to make: "I think there's a search capability here," "I noticed an algorithmic region in `ranker.py`," "this looks like an external API call to OpenAI."
A single explorer typically emits multiple findings of mixed kinds.

```yaml
explorer: <name>
status: ran | not_applicable | failed
status_reason: <one-line, only when not ran>
findings:
  - kind: capability_candidate | overlap | external_surface_candidate | 
      algorithmic_region | infrastructure | anomaly | <custom string>
    references:
      - path: <relative path>
        object: <optional — class, function, class.method>
        lines: [<start>, <end>]    # optional
        relationship: primary_implementation | entry_point | caller | callee | 
          consumer | producer | test | config | schema | bridge | <custom>
        rationale: <optional, brief — why this specific reference>
    rationale: <required, brief — overall reasoning for this finding>
    signals: [<explorer-specific signal names>]
    confidence: high | medium | low
```

### Field notes

- **`kind`** — canonical values listed above; explorers may emit custom string kinds when something genuinely novel surfaces.
  The synthesizer treats unknown kinds as `anomaly`-class for processing but preserves the original label for user display.
- **`references`** — flexible code pointers.
  File-level alone is fine; object-level (function/class/method) preferred when the explorer has that grain; line-level optional.
- **`relationship`** — captures the reference's role in _this finding_.
  The set above; explorers may add custom relationships when needed.
- **Capability naming** — explorers do NOT commit to capability names.
  They emit signals (file overlaps, hub identifiers, signal co-occurrence).
  The synthesizer assigns canonical names from heuristics across explorers.
  This makes overlap detection cleaner (file/object intersection > name match).
- **`rationale`** — brief; one sentence or fragment.
  Per-reference rationale only when distinct from finding-level rationale.
- **`signals`** — free-form per explorer (each explorer's own taxonomy).
  Synthesizer reads signals across findings to detect alignment ("graph signal `community_overlap_high` + port signal `shared_interface` → strong agreement").
- **`confidence`** — explorer self-assessment.
  Different explorers measure differently (graph modularity ≠ AST heuristic); the synthesizer's cross-explorer agreement count is the real confidence signal.

### Worked example

Call-graph explorer output (excerpt):

```yaml
explorer: call-graph
status: ran
findings:
  - kind: capability_candidate
    references:
      - path: src/search/service.py
        object: SearchService
        relationship: primary_implementation
      - path: src/search/scoring.py
        object: tfidf
        relationship: callee
      - path: src/api/handlers.py
        object: handle_search
        relationship: entry_point
    rationale: Tight community of 3 nodes with hub at SearchService; entry point
      identified.
    signals: [community_id_3, hub_density_high, modularity_score_0.42]
    confidence: high

  - kind: algorithmic_region
    references:
      - path: src/search/scoring.py
        object: tfidf
        lines: [42, 80]
        relationship: primary_implementation
        rationale: Threshold and decay constants
    rationale: TF-IDF computation with hand-tuned thresholds.
    signals: [hand_tuned_constant_count_2]
    confidence: medium
```

## Synthesizer

The synthesizer consumes all explorer outputs and produces the capability menu.

Its job:

- Reconcile cross-explorer findings via reference overlap and signal co-occurrence
- Assign canonical capability names from heuristics
- Surface axis disagreements (where explorers proposed conflicting boundaries)
- Identify gotchas (god-modules, single-cluster degeneracy, missing language coverage)
- Estimate per-capability cost (line count, token estimate, file count)
- Propose primary owners for overlaps (default: capability with most edges to bridge wins; ties default to alphabetical order)

### Synthesizer output (capability menu)

> The detailed shape of the synthesizer's output is pending validation through experiment.
> Current target structure (subject to refinement):

```yaml
capability_menu:
  - name: <canonical name assigned by synthesizer>
    files_in_scope:
      - <path>
    evidence_per_axis:
      call_graph: <summary of call-graph findings supporting this capability>
      port_interface: <summary>
      ...
    overlaps:
      - with: <other capability name>
        kind: call | state | port
        proposed_owner: <capability name>
        bridge_references: [<path/object>]
    external_surfaces:
      - kind: consumed | exposed
        identifier: <e.g., "stripe.charges.create" or "POST /users">
        confidence: high | medium | low
    cost:
      file_count: <int>
      line_count: <int>
      token_estimate: <int>
    axis_disagreements:
      - description: <e.g., "graph clusters A+B together; ports separate them">
        explorers: [call-graph, port-interface]
        resolution_prompt: <suggested user question>

gotchas:
  - kind: god_module | single_cluster | language_uncovered | explorer_failed | <custom>
    description: <prose>
    affected_capabilities: [<names>]
```

The synthesizer emits structured markdown matching this conceptual shape; a JSON/YAML schema is not required (the orchestrator and synthesizer share an LLM session).

## Loop semantics

The orchestrator presents the capability menu to the user **only when an escalation condition fires** (see `SKILL.md` § Phase 3).
For runs with no flagged conditions, the orchestrator commits the synthesizer's defaults silently and proceeds to per-capability derive.

When the user is prompted, they may:

- **Continue** — accept the menu and proceed to per-capability derive
- **Loop** — request refinement

If the user requests refinement, the orchestrator must clarify the request unless it is entirely unambiguous.
Refinement options, by cost:

- **Synthesizer-only re-run (cheap)** — apply new synthesis instructions to the existing explorer outputs (e.g., "treat A and B as one capability", "promote the test-suite signals to higher weight")
- **Single-explorer re-run (medium)** — re-run one explorer with adjusted scope (e.g., "ignore `vendor/`", "expand to include `examples/`")
- **Full re-explore (expensive)** — re-run all explorers, typically when scope changes substantively

The orchestrator confirms the chosen refinement type before dispatching.

### Synthesizer escalation flags

The synthesizer's output MUST surface any condition that warrants user prompt.
The orchestrator reads these flags and decides whether Phase 3 escalates or proceeds silently.

Flags the synthesizer emits (when applicable):

- `escalation: single_cluster_degeneracy` — call-graph found one giant community; the synthesizer fell back to alternative partitioning.
  User must confirm the axis.
- `escalation: axis_disagreement` — explorers proposed materially different boundaries (e.g., call-graph clusters A+B together; ports separate them).
  User picks resolution.
- `escalation: low_confidence` — capability candidates' average confidence is below `medium`.
  User confirms the menu is usable.
- `escalation: external_surface_split` — an external-surface candidate has explorer-confidence split (one says owned, one says 3rd-party).
  User classifies.
- `escalation: cost_threshold` — capability count > 6 OR file count > 100.
  User confirms cost.

Absent any flag, the orchestrator proceeds with all synthesizer defaults applied (selection, overlap ownership, external-surface classification).

## Pre-flight cost accounting

Total dispatches for a typical run:

```text
N explorers + 1 synthesizer + 2 × selected_capabilities
```

The orchestrator surfaces this in the Pre-flight Consent prompt when the threshold (capability count > 3 OR file count > 50) is exceeded.

## Single-cluster degeneracy

When the call-graph explorer reports one giant community covering most of the codebase, the synthesizer must NOT silently fall back to single-pass derive.
Instead, switch the partitioning axis:

- File-system structure (directory boundaries)
- Module/package boundaries (language-aware)
- Hub-node ego-networks (top-K hubs, each as a synthetic capability with its 1-hop neighborhood)

For polyglot codebases (multiple languages detected), refuse single-cluster fallback entirely: emit one capability per language root, treat inter-language calls as external surfaces.

The synthesizer surfaces this as a `gotcha` so the user knows decomposition was non-trivial.
