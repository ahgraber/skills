# `diverge` Move

Offer 2–3 approaches with trade-offs.
Lead with a recommendation.

## Lead against the lean

If the user has expressed a preference for option X, present the case for **not-X first**, then X.
Forces honest comparison instead of post-hoc justification of where they were already going.

This is the cheapest agent-sycophancy mitigation: by structuring the answer against the user's lean, you can't accidentally fold to it.

## Shape-distinct constraint

Options must vary on the **load-bearing axis** — not three flavors of one shape.

For an offsite session, the load-bearing axes might be:

- Format (talk / workshop / sim)
- Social structure (solo / paired / panel)
- Artifact (none / runbook / decision)

Three "workshop" options with minor parameter changes is one option, not three.

**Self-check:** if your three options collapse to one decision when you squint, regenerate.

## Batched divergence

When the user signals open exploration ("what could this look like?", "give me everything"), batch multiple `diverge` rounds before any `steelman`.
Premature critique during divergence suppresses idea remoteness ([FlexMind, arxiv:2509.21685](https://arxiv.org/abs/2509.21685)).

When the user signals decisiveness ("I'm leaning toward X, sanity-check it"), single `diverge` round → straight to `steelman`.

## When `diverge` isn't enough

If the option set still feels like default LLM output — three plausible-but-modal answers to the prompt — escalate to `lateral` (parallel subagents).
`diverge` is in-thread; it cannot escape the framing of the conversation that produced it.
`lateral` is the divergence mechanism for genuine novelty.

## Failure modes

- Recommending the user's lean without first arguing against it
- Three options that are the same shape with different parameters
- Critiquing options inline during `diverge` instead of in a separate `steelman` pass
- Skipping `lateral` when the option set is obviously homogeneous and stakes justify dispatch cost
