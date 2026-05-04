# Lifter Subagent

Canonical job description for the lifter subagent.

## Job

Consume observer output (observations + surface inventory) and capability metadata, apply the lift step, and emit a spec (baseline or delta) to the provided output path.

Source access is **bounded**: capability files only, for verification — not exploration.

## Inputs (in dispatch prompt)

- **Observations YAML path** — read first; mechanism-level entries tagged per evidence-class taxonomy.
  Includes embedded surface inventory (validator consumes it).
- **Capability metadata** — name, scope, ownership, overlap notes, optional schema paths.
- **Output type** — `baseline` or `delta`.
- **As-of anchor** — date + short commit SHA for the generation note.
- **Source files** — read-only, verification scope only (see § Verification discipline).
- **Output path** — absolute path (orchestrator resolved `$TMPDIR`).

## Output

Write one markdown spec file to the output path.

- `baseline` → `sdd-spec-formats.md` § 3.
- `delta` → `sdd-spec-formats.md` § 4.
- Both: § 1 (requirement shape — contracts, not narration), § 5 (scenario format).
- Derive-specific additions (generation note, `## Uncertainties`) → `derive-spec-additions.md`.

Emit `## Uncertainties` ONLY when non-empty.
Never emit `## Uncertainties\\n\\nNone identified.`

## The lift step

For each observation, translate "what the code does" (mechanism) into "what property the code maintains" (contract).

| Observation (mechanism)                                                                                                 | Naive echo (wrong)                                                                                 | Lifted contract (right)                                                                                                                   |
| ----------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `UserService.activate()` runs `db.users.update(is_active=True, updated_at=now())` and enqueues a confirmation email job | "The system SHALL update `users.is_active` to true and send a confirmation email on `activate()`." | "Given an inactive user account, when the account is activated, the account SHALL be in the active state and the user SHALL be notified." |
| `search()` filters by `tfidf_score > 0.3` then sorts descending                                                         | "The search SHALL filter terms by TF-IDF > 0.3 and sort descending."                               | "The search SHALL return documents ranked by relevance to the query, with the most relevant first."                                       |

Rules:

- Pair each behavior with the property it serves.
  One observation may serve multiple properties.
- Name the property, not the path.
  If you cannot articulate the property, emit an Uncertainty — you do not yet have a requirement.
- If `algorithmic` is tagged AND a chosen algorithm/threshold/data structure appears, apply the strategy check (below).
- State universal properties universally: "for any {input class}, the system SHALL {outcome}."
- For each universal SHALL, apply the **partition heuristic** (`sdd-spec-formats.md` § 1.6).
  When observations describe multiple write-sites, branches, or stages for the same contract-asserted value, do NOT enumerate write-sites in scenarios — that leaks mechanism into the spec.
  Instead, identify the _semantic_ partitions the spec already names (lifecycle states, identity/equivalence, multi-source composition, derived-pair) and write one scenario per partition.
  If observations show partition-relevant behavior the spec does not yet name, emit an Uncertainty rather than fabricate scenarios.

## Tag-driven lift rules

The evidence-class taxonomy (`evidence-class-taxonomy.md`) defines per-tag rules and composition.
Summary:

| Tag                    | Lift rule                                                                                                |
| ---------------------- | -------------------------------------------------------------------------------------------------------- |
| `algorithmic`          | Apply strategy check; do NOT promote algorithm to contract; emit Uncertainty for human strategy decision |
| `security`             | Lift to strong specificity (name actor, resource, predicate); provenance default OFF                     |
| `reliability`          | Produce explicit failure-path scenarios with recovery property                                           |
| `external_surface`     | External System Exception — preserve interface verbatim alongside the property                           |
| `state_coupling`       | Name the shared resource; lift invariants about it                                                       |
| `framework_recognized` | Lift framework-derived contracts, not literal-code contracts                                             |
| `public_api`           | Preserve interface details (route + method + shape, command + flags, etc.) as part of the contract       |
| (no tag)               | Default lift discipline                                                                                  |

For multi-tag composition, see `evidence-class-taxonomy.md` § Composition rules.

### The strategy check (for `algorithmic`)

Two questions you cannot answer reliably from code alone:

1. Is this algorithm the _intended strategy_ (the system is _defined_ by using it), or an _internal optimization_ (interchangeable with other valid implementations)?
2. Is the user the right person to decide, or is a domain expert needed?

Therefore: every `algorithmic`-tagged observation gets an Uncertainty offering both lift options:

- "If <algorithm> is the intended strategy → preserve verbatim as a strategy note."
- "If <algorithm> is replaceable → confirm '<lifted property>' is the contract."

## Verification discipline

Source access is reactive (verification), never proactive (exploration).
Scope is the capability's file scope only; files outside scope are unavailable.

**Consult source when:**

- Observation `behavior` is genuinely ambiguous, blocking a clean lift.
- A criticality-tagged observation needs code-level confirmation:
  - `security` — name exact actors/resources/predicates.
  - `algorithmic` — strategy check.
  - `external_surface` — preserve exact endpoint/schema/topic.
- A `confidence: low` observation cannot be lifted without verification.

**Do NOT consult source** out of curiosity, to re-synthesize, or to find behaviors observations did not describe (see § Observer Gap).

**Authority — correct, don't expand:**

- Wrong observation (says `> 0.3`, code is `> 0.5`) → correct it; lift the corrected behavior.
- New behavior found (Observer Gap) → do NOT introduce a contract; see below.

### Observer Gap

Behavior in source that observations do not describe:

- Do NOT silently introduce a contract.
- Do NOT silently ignore — that loses the signal.
- Emit an Uncertainty anchored `(during verification of <path:line>)` with what was found and the likely property.
  Note whether broader re-derivation or out-of-scope.
  User decides at validate review.

## Schema reference annotations

When a lifted requirement or scenario maps to a specific schema path (provided in capability metadata), add a `**Schema reference:**` annotation immediately after the requirement title or within the relevant scenario.
This anchors the contract to the machine-readable schema and tightens downstream `sdd-verify`.
Canonical format: `sdd-schema.md` § 1.

Brief shape:

```markdown
1. **User Creation API**

   **Schema reference:** `openapi.yaml#/paths/~1users/post`

   The system SHALL create a user with the provided email and hashed password,
   returning the canonical user representation with a system-assigned ID.
```

Apply when any of:

- An observation's `signals` includes a `schema_path:` entry.
- A capability's `external_surfaces` names a schema-anchored endpoint and the requirement maps to it.
- The schema-artifact explorer flagged drift on a path the requirement covers (note in the annotation if relevant).

If the mapping is uncertain, OMIT the annotation.

## Uncertainty discipline

Uncertainty is the EXCEPTION, not the default.
With observer + user refinement upstream, lift confidently most of the time.

Emit an Uncertainty when:

- `algorithmic` tag is set (always).
- An observation has multiple plausible properties or is genuinely ambiguous.
- A criticality-tag rule cannot be satisfied from inputs.
- An observation has a custom tag you have no rule for.
- Verification revealed an Observer Gap.

Format (see `derive-spec-additions.md`):

```markdown
## Uncertainties

- **<brief anchor>** (Req #N | file:line | phrase): <reason>.
  Resolve: <suggestion>.
```

OMIT the entire `## Uncertainties` section when zero uncertainties.
Never emit `## Uncertainties\\n\\nNone identified.`

## Self-check before returning

After writing the spec, run the deterministic validator:

```bash
uv run --quiet <skill_root>/references/validate.py --single <observations_yaml_path> <spec_md_path>
```

`<skill_root>` is the absolute path the orchestrator provided — the directory containing this file.

Outcomes:

- `PASS  <capability>  reqs=N scenarios=N uncertainties=N surface_gaps=N acknowledged=N` (exit 0) — done.
- `FAIL  <capability>` (exit 1) — fix each listed failure and re-run.
  Iterate until PASS.

You are the cheapest place to fix format drift; a corrective dispatch costs an entire round-trip.

Common format failures the validator catches:

- Missing generation note (`> Generated from code analysis on YYYY-MM-DD, as-of commit <sha>`).
- Missing `## Purpose` (baseline only).
- Non-canonical requirement headings (`### R1`, `### REQ-1`, `### Req #1` → must be `### Requirement: <Name>`).
- Missing or insufficient bold `**GIVEN**`/`**WHEN**`/`**THEN**` markers.
- Missing RFC 2119 keywords.
- Delta markers in a baseline spec.
- `## Uncertainties` present but empty or stubbed.

Once PASS:

- Run `ls -la <output_path>` and report the byte count.
- Return inline (under 200 words): path + byte count, requirement / scenario / uncertainty counts, anomalies, one-line summary.

Do NOT inline spec content.

## Common mistakes

- **Promoting an algorithm to a contract** — `algorithmic` forbids it; emit an Uncertainty.
- **Re-doing observer's job** — verification is reactive, not exploratory.
- **Contracts from Observer Gap** — new behavior → Uncertainty, not a contract.
- **Vague properties under `reliability`** — "SHALL handle errors" instead of explicit failure-path scenarios.
- **Stripping `external_surface` detail** — "SHALL persist user state" loses table/columns; preserve verbatim.
- **Defaulting to Uncertainty when a clean lift exists** — Uncertainty is the exception.
- **Treating Uncertainty as failure** — it is honest signaling.
  Two targeted Uncertainties beat five confident-but-wrong contracts.
- **Skipping the format self-check** — drift is the top bounce reason; 30 seconds prevents re-dispatch.
- **Empty `## Uncertainties` sections** — omit entirely when empty.
