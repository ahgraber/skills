# `lateral` Move

Dispatches parallel persona subagents in isolated context for genuinely novel angles.
Narrate-then-dispatch when fire-conditions are met — do NOT ask permission first.
The fire-conditions below are the gate; the user redirects on the next turn after seeing subagent output, not before dispatch.

## Why parallel subagents

Context isolation is the point.
An in-context "lateral pass" cannot escape the main thread's framing — it shares the very context that needs escaping.
Parallel subagents are Pareto-better than in-context lateral passes for _creative divergence_ even though they're worse for _reasoning critique_ (where in-context wins).

This is also the primary mitigation for LLM creative homogeneity: post-RLHF probability sharpening pushes single-context responses toward modal answers ([Padmakumar & He, arxiv:2502.20408](https://arxiv.org/abs/2502.20408)).
Parallel isolated personas + verbalized sampling + MMR selection is the inference-time stack with the strongest evidence ([VS, arxiv:2510.01171](https://arxiv.org/abs/2510.01171); [diversity-aware retrieval, arxiv:2502.09017](https://arxiv.org/abs/2502.09017)).

## Fire conditions

**Default OFF.**
Dispatch only when:

- The user explicitly asks for lateral angles / parallel personas / novel reframings, OR
- At least TWO of these signals align:
  - Option set in the previous `diverge` looked homogeneous (three flavors of one shape)
  - High-ambiguity domain where the modal answer is obviously inadequate
  - Stakes justify the subagent dispatch cost (user signaled real time/attention investment)
  - User has requested additional ideation ("more options", "what else?", "keep going")

Skip when:

- User has already converged
- Decision is narrow / time-constrained
- Low-stakes refinement of a clear approach
- Only a single soft signal fires — that's the same subjective read that produced the homogeneous set; don't trust it alone

When the conditions are met, narrate the dispatch in one line and fire — do not ask permission.
When they aren't met, don't fire.

## Persona roster

Three default lenses, all domain-agnostic — must be instantiated for the current problem before dispatch.

- **Cross-Pollinator** — imagines how an expert from a wildly unrelated field would tackle this.
  Good for borrowing structural patterns across domains.
- **Analogist** — asks "what is this like in [unrelated domain]?"
  (nature, cooking, sports, architecture, jazz, games, storytelling).
  Good for structural reframings.
- **Trickster** — child-like literal curiosity fused with mischief.
  Asks dumb/obvious questions, subverts framing, proposes the "wrong" version to expose hidden assumptions.

User can specify custom personas ("a cynical marketer", "a safety lawyer").
Honor the request; instantiate richly.

## Persona-distance selector

Same-domain persona panels underperform domain-spread ones ([Choosing Your Experts, arxiv:2509.20553](https://arxiv.org/abs/2509.20553); [Cambridge Design Science 2025](https://www.cambridge.org/core/journals/design-science/article/enhancing-design-concept-diversity-multipersona-prompting-strategies-for-large-language-models/3B346E253508337A4EE899499BE49D9B)).

When picking the 2–3 personas to dispatch:

- Maximize inter-persona conceptual distance, not just per-persona richness
- Reject roster combinations where two personas would obviously converge
- "Three creative roles" is wrong; "one structural / one social / one mischief" is right

The Cambridge result also confirms: **parallel >> sequential >> collective** (single prompt with N roles is the _worst_ strategy).
Always dispatch in parallel; never collapse personas into one prompt.

## Rich instantiation, not role tags

Thin role tags ("act as a marketer") are coin-flip and sometimes harmful ([persona double-edged sword, arxiv:2408.08631](https://arxiv.org/abs/2408.08631)).
Rich instantiation — specific framing that smuggles in task-relevant context — drives the actual gains.

Examples (illustrative, not a fixed mapping):

| Domain                | Cross-Pollinator                                          | Analogist                        | Trickster                                        |
| --------------------- | --------------------------------------------------------- | -------------------------------- | ------------------------------------------------ |
| Software API design   | a restaurant kitchen expediter handling concurrent orders | like a library card catalog      | what's the worst possible endpoint? now invert   |
| Blog post ideas       | a stand-up comedian writer prepping a set                 | like a concept album             | what if the whole premise were a lie?            |
| Lunch-and-learn topic | a children's TV host explaining something complex         | like a magic trick with a reveal | what if you taught it backwards?                 |
| Kids' activity        | a tabletop game designer                                  | like a treasure hunt             | what would cause the most productive chaos?      |
| Product naming        | a poet working under a tight meter                        | like a band name                 | what's the worst possible name that still works? |

## Verbalized sampling — required in subagent prompts

Each subagent generates angles **with internal probabilities**, not just a top-k list.
1.6–2.1× diversity uplift, training-free, ~20 tokens overhead ([VS, arxiv:2510.01171](https://arxiv.org/abs/2510.01171)).

Prompt template fragment:

> Generate 5 angles or reframings, each annotated with the probability you'd assign it as your response if asked freely.
> Include both high- and low-probability angles.
> Do NOT restrict to high-probability ones — low-probability angles are explicitly desired.

## NEVER show probabilities to the user

Probabilities are the orchestrator's calibration signal for selection, weighting, and dedup.
They are NOT for user consumption.

Showing arbitrary numerical probabilities to the user during ideation:

- Creates false precision (the numbers are not calibrated; they reflect the subagent's self-report under VS framing)
- Anchors the user to specific options before they've engaged with the substance
- Imports a "scoring" frame into a divergent step where it doesn't belong

The orchestrating agent **strips probabilities** when synthesizing the final list for the user.
The user sees angles only, in selection order.

## Subagent prompt template

Each subagent receives:

- **Problem frame** — concise summary from the case file (`understood`)
- **Approaches so far** — current option set from `diverge`
- **Persona instantiation** — specific, domain-fitted (NOT a one-line role tag)
- **Task** — produce 5 angles with internal probabilities (verbalized sampling)
- **Anti-default framing** — _"Reject angles that feel like default LLM output._
  _Produce reframings the main thread would not have generated._
  _If your output could plausibly come from a single-pass response to the original prompt, you've failed the assignment."_
- **Output constraint** — angles and reframings only, NOT full designs

## Synthesis — MMR/DPP selection over the merged pool

After subagents return:

1. Concatenate all returned angles (with their probabilities, for internal use only)
2. Embed each angle
3. Greedy-select for inter-angle distance using MMR (or DPP for higher-quality diversity if pool > ~30)
4. Deduplicate semantically near-identical angles; flag angles surfaced by multiple personas (stronger signal)
5. **Strip probabilities** from final list
6. Present 4–6 selected angles to the user alongside the original `diverge` options

The user decides whether any angle is worth developing into an approach.

## Failure modes

- Firing when fire-conditions aren't met (user signaled decisiveness, narrow decision, time-constrained, low-stakes)
- Asking permission instead of narrating-then-dispatching when conditions ARE met
- Thin role tags (the persona table above is the _minimum_ instantiation richness)
- Same-domain panel (e.g., three "creative" roles) instead of domain-spread
- Sharing roster with `steelman` — convergent and divergent passes need distinct personas (see `steelman.md`)
- **Showing probabilities to the user**
- Skipping the MMR/DPP selection step (presenting raw subagent output is noisy)
- Treating persona output as full solutions rather than angles
- Running all three personas when one would do — dispatch cost matters in cheap decisions
