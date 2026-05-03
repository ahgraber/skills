---
name: parallel-subagent-path
description: Dispatch playbook for running sdd-verify Phases 4–6 across isolated subagents. Loaded by SKILL.md when the parallel-path availability gate triggers.
---

# Parallel Subagent Path

Phases 4–6 of `sdd-verify` (Evidence, Contract, Coverage) are per-requirement and amenable to context isolation across subagents.
Phases 2 (Test Suite), 3 (Schema Snapshot), 7 (Conformance), and 8 (Coherence) stay orchestrator-only — they are whole-change checks, not per-requirement.

> **Harness note.** This document uses `Agent` as the running example name for the subagent dispatch tool, and `model` as the example name for a per-dispatch model parameter.
> The skill assumes a Claude-Code-style harness in which subagents inherit Read access from the parent and accept a `model` override.
> If your harness exposes a different dispatch primitive, substitute equivalents — but verify the inheritance and override behavior before relying on this section.

## 1. Availability Gate

Run this once after Phase 2 completes.

1. Confirm the `Agent` tool is available in this session.
2. Count delta spec requirements across all capabilities in scope.
3. Apply the table below in order — first match wins, no ambiguity.

| Order | Condition                                                                              | Path                                        |
| ----- | -------------------------------------------------------------------------------------- | ------------------------------------------- |
| 1     | `Agent` tool unavailable                                                               | Single-agent (skip this path)               |
| 2     | Phase 2 test suite failed and the run is **not** proceeding under a recorded override  | Single-agent (fix tests first)              |
| 3     | Phase 2 test suite failed under override, but the overridden blockers are not explicit | Single-agent (dispatch inputs insufficient) |
| 4     | ≤3 requirements total **and** ≤2 capabilities                                          | Single-agent (overhead too big)             |
| 5     | Otherwise                                                                              | Propose parallel path to user               |

The order is important: tool availability and unsupported Phase 2 failure states short-circuit before requirement counts apply.
The remaining rows partition the supported states, so there is no ambiguous case at this gate.

## 2. Propose Granularity

When the parallel path applies, the orchestrator proposes a granularity to the user.

| Granularity         | One subagent per…      | When to propose                                                                                                                                                                                          |
| ------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Per-capability**  | delta spec capability  | Default. Requirements within a capability typically share context (same baseline spec, same code area), so co-locating them in one subagent reduces total tokens.                                        |
| **Per-requirement** | individual requirement | Propose when a single capability has many (8+) heterogeneous requirements, when requirements span unrelated subsystems, or when one requirement is so large it would dominate a per-capability subagent. |

**Hard cap on concurrency:** dispatch no more than **8 subagents in a single message.**
If the chosen granularity would exceed 8, batch into rounds of 8 and run rounds sequentially, or fall back to per-capability granularity.
Most harnesses degrade or error past this count.

**No mixed granularities.**
Pick one and apply uniformly across the whole change.

Suggested phrasing:

```text
This change has <N> requirements across <K> capabilities. I can verify them in parallel:
- Per-capability (<K> subagents) — recommended when requirements within a capability share context.
- Per-requirement (<N> subagents) — recommended when requirements are heterogeneous or independently large.
Which do you prefer? (Or: stay single-agent.)
```

Do not silently default — surface the choice.

## 3. Resolve the Model

If the dispatch schema exposes a `model` parameter:

- If the user specified a model earlier in the conversation, reuse it across every dispatch.

- Otherwise, ask once before dispatching, then apply the answer uniformly:

  ```text
  Subagent dispatch supports a model override (e.g., `opus`, `sonnet`, `haiku`).
  Which should I use for verify? I'll reuse it across every subagent dispatched.
  ```

- Do not silently fall back to the runtime default.

If the dispatch schema does not expose a `model` parameter, skip this step entirely and proceed to dispatch.

## 4. Dispatch Protocol

Dispatch all subagents in a **single message** with multiple `Agent` tool calls so they run concurrently.
The canonical job description for each subagent lives at `references/verify-subagent.md`.
The shared evidence rules live at `references/evidence-rules.md`.
Dispatch **by reference** — point each subagent at those files rather than inlining the rules, so the contract stays in one place.

Resolve the skill's install path (e.g., `~/.claude/skills/sdd-verify/`, `.claude/skills/sdd-verify/`, or a plugin directory) and substitute it into the template below.
Subagents must be able to read both the dispatch reference and the evidence rules; in a Claude-Code-style harness this is automatic via inherited Read access.

Subagent prompt template:

```markdown
You are a verify subagent.

Read these two files end-to-end before doing any work:

1. `<resolved_skill_root>/references/verify-subagent.md` — your job description.
2. `<resolved_skill_root>/references/evidence-rules.md` — tier definitions, sufficiency rule, citation format.

Your specific scope:

- Requirements in scope: <requirement names or IDs>
- Delta spec path(s): <`.specs/changes/<name>/specs/<capability>/spec.md`, …>
- Baseline spec path(s): <`.specs/specs/<capability>/spec.md`, …>
- Test suite result: pass | no-test-suite | failing-suite-override
- Test execution log: <path to captured per-test-ID output produced in Phase 2, e.g. `.specs/changes/<name>/.verify/test-output.log`>
- Overridden blockers: <explicit list of the known failing tests / audit findings / gate outcomes the user chose not to let block sync, or "none">
- Test artifact listing: <paths to test source directories or files, e.g. `tests/`, `src/__tests__/`>
- Schema diff (if any): <path to `.specs/changes/<name>/schemas/after/` or "none">
- Verification waivers relevant to your scope: <inlined entries from design.md § Verification Waivers, or "none">
- Skill root: <resolved absolute path>

Return findings inline per the format in `verify-subagent.md` § Output.
Do not write to disk.
Do not modify code, tests, or specs.
```

When `Test suite result` is `failing-suite-override`, the orchestrator must also tell the subagent that later-phase conclusions are advisory rather than a clean verification pass.

If the harness recognizes the literal phrase `Think hard.` as a thinking-budget hint, append it after the scope block.
This is Claude-Code-specific; omit on harnesses that do not recognize it.

## 5. Synthesis

After all subagents return:

1. Collect the findings tables.
2. Deduplicate overlapping observations across subagents (e.g., a cross-cutting requirement that appeared in two scopes).
3. Build the canonical per-requirement evidence table from the deduplicated rows — this becomes the **Evidence** section of the final report.
4. Re-key each subagent severity tag (`CRITICAL: …`, `WARNING: …`, `SUGGESTION: …`) into the orchestrator's CRITICAL/WARNING/SUGGESTION report sections.
5. Run Phases 7 and 8 (Conformance, Coherence) on the orchestrator.
6. Assemble the report (Phase 9).

**Do not re-run Phases 4–6 on the orchestrator after subagents have returned** — that defeats the context-isolation benefit.
Spot-check a subagent finding only when:

- A subagent flagged a missing dispatch input (Notes section), or
- A finding's citation looks wrong on inspection (e.g., test path doesn't exist), or
- Two subagents disagreed on the tier of a cross-cutting requirement.

## 6. Common failures specific to this path

- **Dispatching without resolving the model.**
  Silent defaulting hides a cost/quality decision from the user.
- **Mixing granularities.**
  Pick per-capability or per-requirement and apply uniformly.
- **Exceeding the concurrency cap.**
  Batch into rounds of 8 or fall back to per-capability granularity.
- **Re-doing per-requirement work in the orchestrator.**
  Trust subagent citations; spot-check only on the conditions in § 5.
- **Dispatching when Phase 2 failed without explicit overridden blockers.**
  The availability gate forbids this because the dispatch inputs would not delimit what is known-bad versus what can still be analyzed locally.
- **Dispatching a failing-suite override run without telling subagents the overridden blockers.**
  That loses the audit boundary and makes advisory findings look cleaner than they are.
- **Forgetting to surface "missing dispatch input" notes.**
  A subagent that flagged insufficient inputs needs an orchestrator response (re-dispatch with more, or accept INSPECTED), not silent acceptance.
