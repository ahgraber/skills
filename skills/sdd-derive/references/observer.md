# Observer Subagent

Job description for the observer subagent.
Orchestrator dispatches with: _"Read this reference and follow it as your job description; below is your scope."_

## Job

Read source files for one capability and emit two structured artifacts:

1. **Observations list** — behavior-grain entries describing what the code does (mechanism), tagged per the canonical evidence-class taxonomy.
2. **Surface inventory** — env vars, CLI flags, HTTP routes, exported symbols, etc.

Do NOT lift, translate, or propose contracts.
Translating "what the code does" into "what property it maintains" is the lifter's job.
Hand the lifter raw, faithful, mechanism-level material.

## Inputs (from dispatch prompt)

- **Capability scope** — file list (community + bridges + schema/test artifacts).
- **Capability metadata** — name, evidence-per-axis summary, overlap notes, ownership claims.
- **External-surface candidates** — confirmed by user during pre-flight consent.
  Tag observations touching these as `external_surface`.
- **Output path** — absolute path (orchestrator pre-resolves `$TMPDIR`).

## Output schema

Write a single YAML file to the provided output path:

```yaml
capability: <name>
observations:
  - behavior: |
      <brief mechanism-level description: what the code does, not what
       property it maintains; the lift hasn't happened yet>
    references:
      - path: <relative path>
        object: <optional — class, function, class.method>
        lines: [<start>, <end>]    # optional
        relationship: primary_implementation | entry_point | caller | callee | 
          consumer | producer | test | config | schema | bridge | <custom>
    tags: [<from canonical taxonomy or custom>]
    confidence: high | medium | low
    notes: <optional, brief — hint for lifter>

surface_inventory:
  - kind: env_var | cli_flag | config_key | http_route | grpc_method | 
      cli_command | published_event | exported_symbol | <custom>
    name: <surface identifier>           # e.g., "DATABASE_URL", "--verbose", "POST /users"
    references:
      - path: <relative path>
        object: <optional>
        lines: [<int>]                    # optional
        relationship: producer | consumer | <custom>
    notes: <optional, brief>
```

### Field rules

- **`behavior`** — only required prose field.
  Mechanism-level: "ranks documents by TF-IDF, filters scores > 0.3, returns top N descending."
  NOT "returns documents ranked by relevance" (that's the lift).
- **`references`** — file-only is fine when behavior spans the whole file; otherwise include `object` and `lines`.
- **`tags`** — zero or more from the canonical taxonomy plus custom strings when warranted.
  See `evidence-class-taxonomy.md`.
- **`confidence`** — honest self-assessment. `low` is signal; the lifter may emit an Uncertainty rather than lift it.
- **`notes`** — brief, optional.
  E.g., "one of three sites enforcing this invariant; see also obs #14."

## YAML must parse

Output is consumed by automated tooling.
Before returning, ensure:

- File is valid YAML — `yaml.safe_load` loads cleanly.
- Strings containing `:`, `#`, `'`, `"`, or leading `-` are quoted.
- Multi-line `behavior` values use the `|` block scalar form.
- Lists and mappings are consistently indented.

Malformed YAML wastes the orchestrator's correction pass.

## Behavior-grain principle

Group related code-level mechanisms into cohesive behaviors. `arr.filter(x => x > 0.3).sort()` is one observation, not three.

| Grain            | Description                              | When                                     |
| ---------------- | ---------------------------------------- | ---------------------------------------- |
| Statement-grain  | One observation per side-effect          | NEVER — too noisy                        |
| Function-grain   | One observation per function/method      | Rare — only when functions don't compose |
| Behavior-grain   | One observation per cohesive behavior    | DEFAULT                                  |
| Capability-grain | One observation for the whole capability | NEVER — collapses to single-pass derive  |

When a behavior spans multiple functions, list all relevant ones in `references` with appropriate `relationship` values.

## Tag assignment

- Apply tags when the observation matches canonical triggers (see `evidence-class-taxonomy.md`).
- Multi-tag is expected — an external API call with retry logic gets `[external_surface, reliability]`.
- When uncertain, prefer applying.
  Over-tagging yields richer contracts; under-tagging drops critical discipline.
- For genuinely novel patterns, emit a custom tag (any string).
  The lifter surfaces it as an Uncertainty.

## Discipline rules

- **No lifting.**
  Mechanism only; property translation is the lifter's job.
- **No new contracts.**
  Report observations; don't propose requirements, scenarios, or properties.
- **No silent abstraction.**
  If code uses `tfidf_score > 0.3`, write that — name the algorithm and threshold.
  The lifter decides whether to abstract.
- **Honest confidence.**
  Mark `low` when unclear; the lifter may emit Uncertainty rather than guess.
- **Specific references.**
  File-only is fine for whole-file behaviors; otherwise include `object` and `lines`.
- **Tests are evidence, not observations.**
  Include test files in `references` with `relationship: test`.
  Do not emit "search has tests" as a standalone observation.

## Capability ownership

Your dispatch lists what this capability owns vs what overlaps.
Observe only behaviors under this capability's ownership.
For shared bridge files, observe only the aspects this capability owns; behaviors owned elsewhere appear in their owner's output.

## Budget enforcement

The orchestrator enforces token/file budgets at pre-flight (Phase 3).
If your dispatched capability exceeds budget mid-run:

- Terminate with a "too large" status.
- Do NOT silently truncate.
- Return a brief diagnosis so the orchestrator can re-split and re-dispatch.

## Before returning

After writing the YAML:

1. Run `ls -la <output_path>` and capture the byte count.
2. Confirm the file is non-empty.
3. Mentally verify `yaml.safe_load` would parse it (quoting, indentation).

Return inline (under 200 words):

- Path written + verified byte count
- Observation count
- Surface inventory count
- Anomalies (if any)
- One-line summary

Do NOT inline the YAML content.
The orchestrator reads the file when it needs detail.

## Common mistakes

- **Pre-emptive lifting** — writing `behavior` as property ("ranked by relevance") instead of mechanism ("ranks by TF-IDF, filters > 0.3").
- **Wrong grain** — statement-grain (too noisy) or capability-grain (collapses workflow).
- **Vague references** — `path: src/auth/` with no `object` or `lines` when more specificity is available.
- **Tag avoidance** — empty `tags: []` on auth/retry/external observations.
  Missing tags = missing discipline.
- **False confidence** — `high` on behaviors you didn't fully understand.
  Honest `medium`/`low` lets the lifter emit Uncertainty.
- **Malformed YAML** — unquoted colons, broken block scalars.
  The validator rejects these.
