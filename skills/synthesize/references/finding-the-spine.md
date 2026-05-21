# Finding the Spine

How to distill a spine, validate one a user supplied, and handle material that has none — the work behind workflow steps 1–3.
The material may be several sources or the ideas within a single piece; "source" below stands in for both.

## Spine vs. imposed meta-frame

A **spine** is an internal organizing frame the material already carries: a constraint, a claim, a recurring metaphor, or a tension that one source articulates and the others implicitly support.

An **imposed meta-frame** is a shape the synthesizer lays over the material from outside it — "stages of grief," "phases of adoption," a hero's-journey arc, a maturity model.
It reads as over-clever because the reader came for the subject matter, not for the synthesizer's framing virtuosity.

The test: _did this frame come out of a source, or out of me?_
If you could attach the same frame to an unrelated set of sources, it is imposed, not distilled.

## Mode 1a — Distill (no spine supplied)

Scan the material for a frame one part states explicitly and the rest support implicitly — across sources, or across the ideas within a single piece.
Look for:

- a **constraint** that, once named, explains why everything downstream behaves as it does (e.g., a shift in what's expensive);
- a **claim** one source argues that the others corroborate, complicate, or qualify;
- a **recurring metaphor** that more than one source reaches for independently;
- a **tension** the sources collectively expose — two of them pulling opposite ways on the same question;
- a **convergence** the set reveals — independent sources or threads reaching the same point from different starting places, where the through-line's force is the _independence_ of the agreement, not any single source's argument;
- a **trajectory** the set traces — a progression across time, versions, or escalating cases where the _order_ of the parts is itself the through-line (dated releases, a capability advancing, a position shifting).
  When the parts are dated or sequenced, test for this before settling on a flatter frame.

Produce **1–3 candidate spines**, each phrased as a sentence (the through-line), not a topic label.
"Topic: caching" is not a spine; "the cache is the real source of truth and the database is its backup" is.

## Mode 1b — Validate (user supplied a spine)

A user-supplied spine is, by definition, an **over-specified** spine.
The default agent behavior is to ratify it and then cram the material to fit — sycophancy plus the same listicle pull, now hiding under the user's authority.
**Validation must be free to fail and override.**
Confirming is one of four possible verdicts, not the expected one.

Test the proposed spine against **every** part — each source, or each idea in a single piece — and return one of:

- **Holds** — the spine is supported across the set _and_ phrased at the right altitude.
  State the support ("holds across all five; sources 2 and 4 are the explicit articulations").
- **Holds but sharpen** — supported across the set, but the phrasing is true-yet-flat: loose, generic, or pitched at the wrong altitude, so it wastes what the material actually shares.
  Keep the user's claim and propose the sharper version the material argues ("holds across all three, but 'X' undersells it — the through-line they share is the narrower Y").
  Distinct from **amend**: here the scope is right and only the wording is loose.
  This is the common result when a user hands you a one-line spine — sharpen it rather than ratifying it flat.
- **Amend** — the spine is close but its scope is off.
  Propose the narrower or broader version the material actually supports, and surface the count ("holds for three of five; the other two are about X, not Y").
- **Doesn't hold** — the set rhymes on something else.
  Name the better-supported spine and present it as the alternative at the step-3 re-pick gate.

**Sharpen or amend?**
If the user's claim survives intact _inside_ the sharper spine — true as a special case, just under-stated — it is **sharpen**, even when you add a structuring axis, tension, or trajectory the one-liner lacked.
If part of the claim is wrong or fails across the set and must be narrowed, widened, or corrected, it is **amend**.

Never silently widen a weak spine to make it fit: "your spine holds for three of five sources" is more useful than a piece that pretends all five agree.

## The no-spine branch (workflow step 2)

Sometimes the material genuinely doesn't rhyme — no internal frame is shared, whether across several sources or across a single piece's ideas.
Do **not** force prose onto material that has no spine.
Gate, and offer the user two honest moves:

1. **Synthesizer-POV spine** — your own frame, named explicitly as a different move: "the material doesn't share an organizing frame; here is one _I_ would impose to argue a point — flagging that it's mine, not theirs."
   This is legitimate when declared.
   It becomes the imposed-meta-frame failure only when it's smuggled in as if it came from the material.
   Even a POV spine must be argued _from_ the material, not used to override it.
2. **Hand back** — recommend a different deliverable: an annotated list, a comparison table, or separate treatments.
   When enumeration is the right answer (see the escape hatch in SKILL.md), say so rather than manufacturing a false through-line.

## Source-earns-its-place

Once a spine is chosen, every part must earn its place under it — each source, or each idea in a single piece.

- A source that supports the spine goes in, carrying the part of the argument it's best at.
- A source that doesn't fit is **named as an exclusion** ("X sits outside this thread because…"), not crammed in to look comprehensive.
- A spine drawn from a single source — or a single section of one piece — can over-weight it.
  Counter it: make the rest do real work under the spine, or acknowledge the spine is mostly that one's and the rest are corroboration.

## Self-interested sources — the grounding pass

Some material isn't neutral: a vendor announcing its own product, a lab promoting its own result, marketing, advocacy.
Its framing is engineered to flatter the result and bury the caveats, so taking the spine straight from it reproduces its spin.

When you detect a self-interested source, **offer the user a grounding pass before committing the spine** — a GATE; surface it, don't run it silently: "these are the vendor's own announcements; want me to ground the through-line against outside context first?"

If the user takes it, the pass reaches **outside** the supplied material to:

- restore the caveats the source downplays;
- check its claims against independent assessments;
- supply provenance or prior events that situate the result.

Fold only the load-bearing findings into the gist, **flagged as external** ("the lab frames this as X; an outside assessment complicates it with Y").

**Fidelity guard.**
Every external claim must be grounded; if you can't verify it, say so rather than assert it — that is why the pass is _offered_, not automatic, and the user is the backstop.
External context enters **only** through this gated pass; it is not a standing license to pad the gist with background.
