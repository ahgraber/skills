# Validate Phase

The validate phase checks the generated specs against three signals: surface coverage, uncertainty count, and Phase 7 quality (format compliance).
It is **deterministic** — runs as a Python script, not a subagent.

Validation runs in two places:

- **Per-capability** (lifter, during Phase 4) — each lifter runs `validate.py --single` against its own output before returning.
  Catches format drift at write time; the lifter fixes failures in place and re-runs until PASS.
  This avoids round-tripping a corrective lifter pass through the orchestrator.
- **Aggregate** (orchestrator, this phase) — once all capabilities have completed, the orchestrator runs `validate.py` across the whole run.
  Aggregate format / YAML / coverage / uncertainty counts feed the final report.
  If lifters did their self-check, format and YAML failures should be zero here; surface gaps and uncertainty totals are the substantive output.

```bash
# Lifter mode (single capability; used inside Phase 4)
uv run --quiet <skill_root>/references/validate.py --single <observations.yaml> <spec.md>

# Aggregate mode (whole run; used at Phase 5)
uv run --quiet <skill_root>/references/validate.py <observations_dir> <specs_dir>
```

## Inputs

- Generated spec(s) — delta or baseline format.
- Surface inventory (per capability, from observer YAML).
- `## Uncertainties` section content (per spec, when present).

## Surface coverage diff

The diff is **kind-aware** — different surface kinds have different coverage expectations.

Public-consumer surfaces (callers depend on these directly):

- `http_route`, `grpc_method`, `cli_command`, `published_event`, `exported_symbol`

Internal-knob surfaces (operator-tunable; lift discipline correctly excludes most of these from contracts per `sdd-spec-formats.md` § 1.3):

- `env_var`, `config_key`, `cli_flag`

Severity rules:

| Surface kind    | Absent from spec entirely                                             | Mentioned but no scenario         |
| --------------- | --------------------------------------------------------------------- | --------------------------------- |
| Public-consumer | **Gap** — flag for user review                                        | **Acknowledged-without-scenario** |
| Internal-knob   | **Acknowledged-without-scenario** (default — lift correctly excluded) | **Acknowledged-without-scenario** |

Why the asymmetry: contracts state what callers depend on, not internal knobs.
A `POST /users` route absent from a baseline `conversion-api` spec is a real gap — external consumers depend on the route.
An env var `AIZK_WORKER_POLL_INTERVAL_SECONDS` absent from the spec is the lifter doing its job — the contract is "a worker SHALL begin processing a queued job within bounded latency", not "polls every 2 seconds."

Examples:

- A `POST /users` route in inventory that doesn't appear in the spec → **Gap** (consumers break if it changes).
- A `--verbose` CLI flag absent from spec → **Acknowledged-without-scenario** (operator ergonomics, not contract).
- An env var `DATABASE_URL` absent from spec → **Acknowledged-without-scenario** (configuration knob).
- An exported symbol `WorkspaceEscape` absent from spec → **Gap** (callers depend on the exception type).

The validate report groups gaps by capability and lists them.
Gaps require user review; acknowledged-without-scenario is informational only.

## Uncertainty review

For each spec, count items in the `## Uncertainties` section (if present).
Surface to user grouped by capability:

```text
Capability "search": 1 uncertainty
  - Search ranking strategy (Req #5): TF-IDF strategy ownership unclear

Capability "billing": 0 uncertainties

Capability "auth": 2 uncertainties
  - Token validation specificity (Req #2): ...
  - Verified gap in src/auth/middleware.py:42: ...
```

A spec with zero uncertainties is the typical, healthy outcome.
A spec with many uncertainties (>5) suggests insufficient observer scope or unclear capability boundaries — surface this as a meta-concern in the report.

## Phase 7 quality checklist

- [ ] Requirements use RFC 2119 keywords (SHALL/MUST/SHOULD/MAY)
- [ ] Scenarios use `#### Scenario:` with **GIVEN**/**WHEN**/**THEN** (bold, exact casing)
- [ ] Each requirement is a lifted contract, not a restatement of code structure — states the property the code maintains, not the code's actions (see `evidence-class-taxonomy.md` for tag-driven rules)
- [ ] Algorithm names, thresholds, and hand-tuned constants do NOT appear in contracts unless `algorithmic` strategy was explicitly preserved (with corresponding Uncertainty resolution)
- [ ] External-surface contracts preserve the external interface verbatim (endpoints, table columns, topic names)
- [ ] Public-API contracts preserve interface details (route + method, command + flags, exported signatures)
- [ ] Reliability-tagged contracts include explicit failure-path scenarios
- [ ] Security-tagged contracts use strong specificity (named actor, resource, predicate)
- [ ] State-coupling contracts name the shared resource with invariants
- [ ] Delta specs (change directory) use ADDED/MODIFIED/REMOVED sections
- [ ] Baseline specs have no delta markers
- [ ] Baseline specs include a `## Purpose` section
- [ ] Each generated spec has a generation note blockquote with date and as-of commit SHA
- [ ] Large surface areas were decomposed into multiple capability specs (verified by checking the synthesizer's capability menu)
- [ ] `## Uncertainties` section is omitted when empty; present and non-empty when uncertainties exist

## Validate report format

The orchestrator emits a brief report after validate completes:

```text
SDD Derive — Validate Report
============================

Capabilities derived: 3 (search, billing, auth)
As-of commit: a1b2c3d
Total requirements: 24
Total uncertainties: 3

Surface coverage:
- search: 0 gaps, 1 acknowledged-without-scenario
- billing: 1 gap (RATE_LIMIT_PER_MINUTE env var)
- auth: 0 gaps

Uncertainties:
- search/spec.md: 1 (algorithmic strategy)
- auth/spec.md: 2 (verified gap, security strong-specificity)

Phase 7 checklist: 14/15 items pass
- Failed: "Each generated spec has generation note" — billing/spec.md missing as-of SHA

Action items for user:
1. Decide on billing rate-limit env var (gap)
2. Resolve 3 uncertainties in search and auth
3. Add generation note to billing spec
```

Action items are listed in priority order: gaps → uncertainties → quality issues.

## When validate triggers re-derive

Validate may surface conditions that warrant re-derivation:

- Many uncertainties in one capability (>5) — observer scope likely insufficient
- Many surface coverage gaps — observer missed enumeration
- Phase 7 quality failures concentrated in one capability — lift discipline failure

The orchestrator does NOT auto-trigger re-derive.
The user decides; re-derive is a user-initiated workflow.
