# Round Playbook

Per-round mechanics, artifact schemas, dispatch templates, and model tiers for the `deep-research` loop.
Read alongside `SKILL.md` (the loop diagram and invariants) and `verification.md` (the review valve).

## Workspace layout

All run state lives under one session directory so raw is retained and re-derivable:

```text
$TMPDIR/deep-research-<session>/
  topic-map.md          # living coherence anchor, updated every converge
  findings-ledger.md    # append-only claims with pointers + verdicts
  raw/
    <dimension-slug>-<n>.md   # verbatim fetched content, one file per source
```

`<session>` is a short slug of the question.
Reuse the same directory across all rounds — never re-fetch a source already in `raw/`.

## Artifact schemas

### topic-map.md

The coherence spine.
Refresh in place at each converge — it is a snapshot, not a log.

```markdown
# Topic map: <question>

date: <current date>  |  temporal precision: <day|week|month|year>  |  loop cap: <N>

## Dimensions

- [open] <dimension> — <why it matters> — open questions: ...
- [saturated] <dimension> — covered; no new signal last round
- [dead-end] <dimension> — pursued, low value; stop
- [new] <dimension> — surfaced this round, not yet explored

## Open questions feeding next round

- ...
```

### findings-ledger.md

Append-only.
One row per claim.
The pointer is what makes synthesis lossless.

```markdown
| id | claim | source-url | raw-pointer | self-tag | verdict | confidence |
|----|-------|-----------|-------------|----------|---------|------------|
| f1 | ...   | <https://…> | raw/foo-1.md#L40-58 | single-source | Uncertain | low |
```

- `raw-pointer` = `raw/<file>#L<start>-<end>` — points into the verbatim dump.
- `self-tag` (set by the search subagent at dump time, cheap triage signal):
  `single-source` | `low-confidence` | `contested-on-its-face` | `primary` | `secondary`.
- `verdict` / `confidence` start empty; the review valve fills them.

## Round-by-round

### R0 — Clarify (skip if already specific)

Ask **at most 5** questions in a **single volley** (use the harness's user-question primitive, e.g. `AskUserQuestion`), then proceed — do not iterate clarification.
Always include a **depth/budget** question; it is the dominant cost lever, so the user owns it.
Phrase it in plain language — never expose internal terms like loop caps or round numbers.
For example:

> How deep should I go?
>
> - **Quick** — one focused pass; fastest, lightest.
> - **Standard** — one round of follow-up to chase gaps and double-check contested claims.
> - **Exhaustive** — keep digging until the findings stop changing.

Map the answer to the follow-up budget that governs the loop:

| User choice | Follow-up rounds allowed                        |
| ----------- | ----------------------------------------------- |
| Quick       | none — a single explore → exploit → review pass |
| Standard    | one                                             |
| Exhaustive  | up to three                                     |

Other good questions: scope boundaries, recency window, audience and depth, must-include or must-exclude angles.

### R1 — Frame (orchestrator, no fan-out)

1. Check the current date in context.
   Map intent → temporal precision and store it in the topic-map (see `temporal-and-output.md`).
2. Decompose the question into dimensions.
   Force breadth with the information-type matrix: facts · examples · expert opinion · trends · comparisons · challenges/criticism.
3. Write `topic-map.md` and an empty `findings-ledger.md`.
   Set the loop cap from R0.
4. State the plan to the user (dimensions, cap, scope).

### R2 — Explore (breadth fan-out)

- Dispatch **one subagent per dimension**, in parallel, in a single message.
- Each subagent: search widely (≥3–5 angles / phrasings), fetch full sources, **dump each source verbatim to `raw/`**, append `{claim, source-url, raw-pointer, self-tag}` rows to the ledger.
  Returns **only** the rows — never raw content.
- Converge (orchestrator): update topic-map — mark saturated/dead-end dimensions, add `new` ones, list open questions.
  **No review this round.**

### R3 — Exploit (depth fan-out) + review valve

- Dispatch deep-dive subagents on high-value threads and follow-the-thread (cited references, named entities, adjacent terms).
  Same dump-raw + pointer-return contract.
- Converge: draft findings **by theme**; flag conflicts and gaps in the ledger.
- **Fire the review valve** (see `verification.md`).
  If it leaves sufficient unresolved questions, go to R4; otherwise go to Synthesize.

### R4 — Expand/Resolve (targeted; bounded by cap)

- For a **contested claim**: targeted re-fetch / additional sources for that claim only;
  re-review just the new material.
- For a **coverage gap**: add the missing dimension and loop back to **R2** (full breadth on
  the new dimension only).
- After the round: **report progress to the user** (ledger diff), then check the cap:
  - under cap **and** a real coverage gap remains → loop to R2.
  - cap reached **or** saturated (no new signal, no unresolved load-bearing claims) → Synthesize.

### Synthesize (terminal)

Read the ledger + topic-map; for any contested or load-bearing claim, **open the raw pointer** and confirm before writing.
Produce the report per `temporal-and-output.md`.
The synthesizer calls **no retrieval tools** and reads **no progress prose** — only artifacts and raw.

## Model-tier map (step-down)

Assign lighter models to mechanical stages and keep judgment on the strongest tier.
Raw retention (invariant 1) is what makes step-down safe — a weak distillation is recoverable from raw.
Tiers below are **capability bands, not specific models**; map them onto whatever provider the harness uses (Anthropic, OpenAI, Google, or other).

| Stage                                                             | Capability band                      |
| ----------------------------------------------------------------- | ------------------------------------ |
| Orchestrator (frame, converge, route, synthesize)                 | flagship                             |
| Explore / exploit search subagents (search, fetch, dump, distill) | mid                                  |
| Narrow single-source fetch / extract                              | light                                |
| Review-valve skeptic verifiers                                    | flagship (mid for low-stakes claims) |

Map the bands to your provider's lineup — flagship / mid / light correspond to, for example, Anthropic's Opus / Sonnet / Haiku, or the equivalent flagship, mid, and light tiers from OpenAI or Google.
The principle is the step-down, not the names: orchestration and verification get the strongest band; high-volume retrieval and distillation get a mid band; narrow extraction gets the lightest.
Set each agent's model with whatever the harness exposes (typically a `model` parameter on the agent or subagent call).

## Saturation — the stop signal

Stop looping when **either** the cap is hit **or** a round adds no new dimensions, no new load-bearing claims, and leaves no contested claim unresolved.
Saturation beats a fixed round count.
When you stop because of the cap rather than saturation, **say so** in the final report's limitations section — silent truncation reads as "covered everything" when it did not.
