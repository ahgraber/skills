# Audit Failure Modes

Run after the first draft (workflow step 5).
Each is a way a spine-led gist collapses back toward a modal answer — the listicle or the fluff-pad.
Detect, then repair in place — repairing a listicle into a spine-led gist is often a rewrite, so catch these early.

## Listicle relapse

**Symptom:** the body has become a numbered or bulleted march through themes/practices, each section self-contained, the spine visible only in the intro.
**Repair:** re-sequence around the spine's logic.
Each section should advance the through-line, not catalog a topic.
If sections can be reordered without loss, the spine isn't carrying them — it's decoration.

## Coverage creep / fluff

**Symptom:** the gist has sprawled past a few tight paragraphs into comprehensive summary; sentences pad, hedge, or relay what a source says instead of distilling insight.
A reader could skim the source for the same thing.
**Repair:** cut to the spine.
Every sentence must carry insight that stands on its own; if it only reproduces what a source contains, drop it and point the reader to the source.
Concision is the deliverable — the more you cut without losing the through-line, the better.
**Do not over-prune:** a quote, table, or figure that crystallizes the spine and stands on its own is the highest-signal support there is — surface it, don't cut it as "reproduction."
Coverage creep is comprehensive expository bulk; a single load-bearing artifact that earns its place is the opposite.

## Abandoned framing

**Symptom:** an organizing image, metaphor, or claim opens the piece and is never seen again; the rest reverts to a topical list.
**Repair:** either carry the frame through every section (it should explain each turn) or drop it from the intro.
A frame stated once and abandoned is worse than none — it advertises a spine the piece doesn't have.

## Quote-as-spine

**Symptom:** a source's quotation is doing the argumentative work the synthesizer should be doing; the piece leans on "as X put it…" at each load-bearing turn.
**Repair:** make the argument in your own voice; use the quote as evidence _for_ your claim, not as the claim.
If removing the quote removes the point, you haven't synthesized — you've forwarded.

## Significance inflation

**Symptom:** superlatives and importance-claims ("striking," "the strongest convergence," "remarkably," "this cannot be overstated") standing in for argument.
**Repair:** replace the adjective with the reason.
If something is the strongest point, show why it outweighs the others; don't assert that it does. (Overlaps with `antislop-writing`'s AI-tells catalog; here the concern is argument substituted by emphasis, not sentence polish.)

## Source taken at face value

**Symptom:** a self-interested source (vendor PR, a lab announcing its own result, marketing) set the framing, and its spin survived into the gist — the caveats it downplays are missing, and its significance claims are repeated as fact.
**Repair:** run the grounding pass (see `references/finding-the-spine.md`): restore the downplayed caveats and check the claims against external context, flagged as external.
If you never offered the user that pass during the scan, offer it now rather than shipping the source's spin.

## Forced-fit spine

**Symptom:** sources crammed under a spine they don't actually support — the fit is asserted, the seams show.
Most common after **validate** mode, where a user-supplied spine was ratified rather than tested.
**Repair:** return to `references/finding-the-spine.md`.
Either amend the spine to the version the material supports, or move the misfitting sources to named exclusions.
A spine that needs every source forced under it is the wrong spine.

## Over-pruned wisdom

**Symptom:** a long-standing practice was dropped because it isn't novel, taking the rationale-shift with it.
**Repair:** re-ground the old practice in its new rationale.
If a practice now matters more, or for a different reason, **naming that shift is the synthesis** — the change in why-it-matters is the load-bearing content, not the novelty of the practice.
Restore it as a rationale shift, not a fact to report.
