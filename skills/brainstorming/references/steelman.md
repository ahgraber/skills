# `steelman` Move

Always runs when a substantive proposal is on the table.
Critique is the convergence mechanism — not a gate before approval.

## Pipeline

1. Pick shape, announce in one line
2. Generate critique material (in-context or cross-context subagents)
3. **Arbiter pass** — agent applies adversarial lenses to synthesize a refined proposal
4. Present refined proposal

## Shape selection

| Shape                                                  | When                                                                                                                                   |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| **Devil's advocate** (in-context, single pass)         | Most cases. Cheap insurance. Identifies assumptions, edge cases, failure modes, alternatives dismissed too quickly.                    |
| **Multi-steelman** (parallel subagents, cross-context) | Approaches were close. Decision is high-stakes or hard to reverse. User explicitly wants thoroughness. **Sycophancy risk is high.**    |
| **Pre-mortem framing** (added to either above)         | Time-sensitive proposals or domains with known historical failure patterns. Frame: "assume this shipped and failed in 6 months — why?" |

Debate (two subagents arguing) is not used.
Evidence: degrades into sycophancy or thought-collapse ([2024–2026 MAD literature: arxiv:2511.07784, arxiv:2509.23055](https://arxiv.org/abs/2511.07784)).
Multi-steelman + arbiter dominates it.

## Cross-context steelman — the anti-sycophancy lever

When risk of agent sycophancy is high (user has expressed strong enthusiasm; agent already softened earlier critique; high stakes), dispatch the steelman as a **parallel subagent that does NOT see the user's reactions to the proposal**.

The subagent receives only:

- The problem frame
- The proposal as written
- The steelman assignment

It does NOT receive:

- The conversation history
- The user's enthusiasm signals
- The agent's prior (possibly softened) critiques

This isolates the critique from the user-pleasing reflex.
Cross-context review measurably outperforms in-context for catching errors ([arxiv:2603.12123](https://arxiv.org/pdf/2603.12123)).

## Distinct roster from `lateral`

If `lateral` ran earlier in the session, `steelman` subagents must NOT share roster with the lateral personas.

Reason: convergent-pass personas re-using divergent-pass personas re-collapses the diverse pool back into the modes that generated it ([HAICo, arxiv:2512.18388](https://arxiv.org/html/2512.18388v2); [CreativeDC, arxiv:2512.23601](https://arxiv.org/abs/2512.23601)).

- **Divergent-pass roster** (`lateral`): cross-pollinator, analogist, trickster, custom (per problem)
- **Convergent-pass roster** (`steelman`): skeptic, adversary, future-self, audience, novice, domain-specialist (per problem)

No overlap.

## Multi-steelman variants (pick one or combine)

- **Steelman-the-alternative** — one subagent builds the strongest case for an approach that was NOT chosen, forcing real comparison
- **Steelman-by-stakeholder** — subagents steelman from specific stakeholder positions ("loudest critic", "security reviewer", "skeptical exec")
- **Steelman-by-constraint** — each subagent argues from a different constraint (cost, speed, maintainability, accessibility, reversibility)

Pick 2–4 subagents.
More than 4 rarely helps and the arbiter struggles to synthesize.

## Subagent prompt template (multi-steelman)

Each subagent receives:

- **Problem frame** — from case file
- **Chosen approach** — full description
- **Steelman assignment** — specific: "steelman approach B", "steelman from a security reviewer's position"
- **Verbalized sampling** — produce concerns with internal severity probabilities
- **Task** — (1) the strongest version of the case, (2) concrete concerns with the chosen approach, (3) what evidence or change would resolve the critique

**Probabilities are for orchestrator use only — never shown to the user.**
The arbiter uses them for severity weighting and dedup; the user sees concerns ranked qualitatively (high / medium / low) or in narrative form.

## Arbiter pass — adversarial lenses

Agent synthesizes critique using lenses as angles (NOT separate subagents — these run in-context):

- **Skeptic** — what's weakest?
  what assumptions are shaky?
- **Adversary** — hostile, malicious, or unintended use; worst interpretation
- **Future-self** — 6 months from now, what will look obvious in hindsight?
- **Audience** — whoever receives the thing (reader, user, attendee, kid, consumer).
  Does it land?
- **Novice** — fresh eyes, no context, jargon-blind.
  What's confusing or implicit?

Pick the 2–4 lenses most relevant for the domain.

- Blog post: audience + skeptic + novice
- Software rollout: adversary + future-self + audience
- Compliance review: skeptic + adversary

## Arbiter output

Refined proposal that:

- Addresses the critique's strongest points (adjusts design or explicitly accepts the trade-off)
- Notes which concerns were declined and why
- Flags residual risks the user should know about
- Strips internal probabilities (orchestrator-only signal)
- Presented in conversation, not as a file

## User response

After the refined proposal, user signals:

- **Accept** → `close`
- **Iterate** → cap at ONE `steelman` cycle per proposal.
  A second round runs only on explicit user request ("push harder", "do another steelman", "what else are we missing").
  An ambiguous nudge defaults to `close` with residual concerns surfaced — further rounds rarely add signal, they add ceremony.
- **Back to options** → another `diverge` round (or `lateral` if homogeneous)

If the user accepts without engaging the trade-offs, log to `engagement` in the case file.
Two consecutive low-engagement acceptances → restate the strongest counter via `name-tension` (self) before proceeding.

## Failure modes

- Sycophantic critique — objections the chosen approach trivially defeats
- Arbiter rubber-stamping without integrating critique into the design
- Using debate shape (degraded vs multi-steelman + arbiter)
- Running multi-steelman for a cheap decision (dispatch cost > value)
- Skipping the arbiter pass — critique without synthesis is just noise
- Picking lenses that don't fit the domain (e.g., "novice" for compliance review between domain experts)
- Treating the refined proposal as the terminal output — `close` still needs to run
- Sharing roster with `lateral`
- Auto-iterating a second steelman round without explicit user request
- **Showing internal severity probabilities to the user**
