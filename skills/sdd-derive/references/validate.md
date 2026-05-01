# Validate Phase

Check generated specs against three signals: surface coverage, uncertainty count, Phase 7 quality (format compliance).
**Deterministic** — runs as a Python script, not a subagent.

## Where validate runs

- **Per-capability** (lifter, Phase 4): each lifter runs `validate.py --single` on its own output, fixes failures in place, re-runs until PASS.
  Catches format drift at write time; avoids round-tripping a corrective dispatch.
- **Aggregate** (orchestrator, Phase 5): once all capabilities complete, run `validate.py` across the whole run.
  Surface gaps and uncertainty totals are the substantive output; format/YAML failures should be zero if lifters self-checked.

```bash
# Lifter mode (single capability; Phase 4)
uv run --quiet <skill_root>/references/validate.py --single <observations.yaml> <spec.md>

# Aggregate mode (whole run; Phase 5)
uv run --quiet <skill_root>/references/validate.py <observations_dir> <specs_dir>
```

## Inputs

- Generated spec(s) — delta or baseline format.
- Surface inventory (per capability, from observer YAML).
- `## Uncertainties` section content (per spec, when present).

## Surface coverage diff

Diff is **kind-aware**: surface kinds have different coverage expectations.

- **Public-consumer** (callers depend on these directly): `http_route`, `grpc_method`, `cli_command`, `published_event`, `exported_symbol`.
- **Internal-knob** (operator-tunable; lift correctly excludes most per `sdd-spec-formats.md` § 1.3): `env_var`, `config_key`, `cli_flag`.

Severity:

| Surface kind    | Absent from spec entirely                                             | Mentioned but no scenario         |
| --------------- | --------------------------------------------------------------------- | --------------------------------- |
| Public-consumer | **Gap** — flag for user review                                        | **Acknowledged-without-scenario** |
| Internal-knob   | **Acknowledged-without-scenario** (default — lift correctly excluded) | **Acknowledged-without-scenario** |

Rationale: contracts state what callers depend on, not internal knobs.
A `POST /users` route absent from a `conversion-api` baseline is a real gap.
An env var like `AIZK_WORKER_POLL_INTERVAL_SECONDS` absent is the lifter doing its job — the contract is "a worker SHALL begin processing within bounded latency", not "polls every 2 seconds."

Examples:

- `POST /users` in inventory but not in spec → **Gap**.
- `--verbose` CLI flag absent → **Acknowledged-without-scenario**.
- Exported symbol `WorkspaceEscape` absent → **Gap** (callers depend on the exception type).

Group gaps by capability.
Gaps require user review; acknowledged-without-scenario is informational.

## Uncertainty review

Count items in each spec's `## Uncertainties` section (if present).
Surface grouped by capability:

```text
Capability "search": 1 uncertainty
  - Search ranking strategy (Req #5): TF-IDF strategy ownership unclear

Capability "billing": 0 uncertainties

Capability "auth": 2 uncertainties
  - Token validation specificity (Req #2): ...
  - Verified gap in src/auth/middleware.py:42: ...
```

Zero uncertainties is the typical, healthy outcome. **>5 uncertainties** in one capability suggests insufficient observer scope or unclear capability boundaries — surface as a meta-concern.

## Phase 7 quality checklist

- [ ] Requirements use RFC 2119 keywords (SHALL/MUST/SHOULD/MAY)
- [ ] Scenarios use `#### Scenario:` with **GIVEN**/**WHEN**/**THEN** (bold, exact casing)
- [ ] Each requirement is a lifted contract, not a restatement of code structure (see `evidence-class-taxonomy.md` for tag-driven rules)
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
- [ ] Large surface areas were decomposed into multiple capability specs
- [ ] `## Uncertainties` section is omitted when empty; present and non-empty when uncertainties exist

## Validate report format

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

Action items in priority order: gaps → uncertainties → quality issues.

## When validate triggers re-derive

Validate may surface conditions warranting re-derivation:

- Many uncertainties in one capability (>5) — observer scope likely insufficient.
- Many surface coverage gaps — observer missed enumeration.
- Phase 7 quality failures concentrated in one capability — lift discipline failure.

The orchestrator does NOT auto-trigger re-derive.
Re-derive is user-initiated.
