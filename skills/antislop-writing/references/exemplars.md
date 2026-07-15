# Register exemplars

Read the exemplars for the jobs your piece does before composing; after drafting, set sample paragraphs beside them.
The target is their texture — how they rank facts, where the short sentences land, when a device is allowed to appear — not their topics or their shapes.
Imitate the stance, not the outline: these passages deliberately differ in shape so that no single structure becomes a template.

Every target passage is quoted from the skill author's published writing (see `ATTRIBUTION.md`), with mechanical tics normalized: hyphens standing in for dashes became em dashes, one redundant "etc." was dropped, one ampersand was spelled out.
What remains — dense parentheticals, informal verdicts, an occasional sentence adverb — are idiosyncrasies of one human writer's prose, not patterns to transfer.
What transfers is the ranking, the rhythm, and the discipline about devices.

Most entries pair the target with a **near-miss**: text that breaks no ban and still reads machine-made.
Learning to see why the near-miss fails is the point of this file.
The last two entries instead pair a target with **the tell** it licenses — the earned use of a device the tells catalog bans — so the discrimination is visible in both directions.

A calibration note: the rhythm and contrast baselines behind the audit tripwires are document-wide averages.
Argument-dense passages like these legitimately run hotter locally; do not read a single excerpt as a per-paragraph quota.

## Explaining a mechanism — vary the rhythm; let a short sentence land

Near-miss (no banned tokens, every clause the same weight):

> Reduced ownership leads to concept drift between the user's intention and the artifact, and over time the user's mental map becomes misaligned with reality, and these effects compound each other, and ownership drift makes the work harder to reengage with, and users therefore increasingly delegate to keep up, and the confident voice of the model encourages more trust and less critical evaluation.

Target:

> Reduced ownership leads to a type of concept drift between the user's intention, the ground truth of the work artifact, and what the AI model produced; over time the user's mental map of their work gets first fuzzier and then misaligned with reality.
> And these effects compound.
> Ownership drift makes the work harder to understand and reengage with, so users increasingly delegate to LLMs to keep up; the confident LLM voice encourages more trust and less critical evaluation of the output; and increased uncritical acceptance amplifies drift.

Two long mechanism sentences frame a four-word pivot.
The closing sentence is a genuine causal loop stated as one — drift makes the work harder, harder work breeds delegation, delegation breeds trust, trust amplifies drift — not a triad for cadence.
The near-miss carries the same facts and no banned tokens; it fails because every clause holds equal rank and no pivot ever lands.

## Arguing — open on the claim; coin the label only after the argument pays for it

Near-miss (the label arrives first and substitutes for the argument):

> The core problem with sharing LLM output is the verification tax.
> Recipients pay a verification tax on every message because models hallucinate, and this tax compounds the effort asymmetry that already burdens readers.
> The verification tax is why raw AI output erodes trust.

Target:

> Before LLMs, trust was the default.
> Authors wrote from their personal expertise and perspective, and readers could judge an author's understanding of the subject based on the coherence of their writing.
> LLMs generate the most probable next token given an overarching goal to be helpful, which explains their propensity for hallucination and why many people feel that LLMs are bullshit generators.
> Modern LLMs are typically provided tools to help them look up grounding information that reduces (but does not eradicate) their likelihood to outright make up facts during their responses.
> But that still doesn't solve the trust problem; the reader still has no way to know what the sender checked and what they didn't.
> LLM responses, therefore, cannot be trusted by default and compound the effort asymmetry on the reader by adding a verification tax.

A six-word claim opens; the mechanism earns it; the mitigation is conceded in a parenthetical; "verification tax" is coined in the last sentence, after the argument has paid for it.
The near-miss uses the same label three times and never makes the argument — a coinage before its argument is the invented-concept-label tell, and the same coinage after is craft.

## Comparing a landscape — an organizing idea, not fragments and not chains

Slop (the catalog reflex):

> #### Semantic Kernel
>
> Microsoft's agent framework. Nonstandard abstractions. Feature churn. Python/Java parity lags.

Near-miss (verbs restored, nothing ranked):

> Langchain is a framework that was difficult to extend, and Semantic Kernel is a Microsoft framework that has nonstandard abstractions and feature churn, and LangGraph, CrewAI, and Pydantic AI are newer frameworks that treat agents as the primary metaphor, and third-generation SDKs incorporate runtime support and improved tools, context management, and memory.

Target:

> Langchain was difficult to extend beyond "here's a demo I made with Langchain".
> Microsoft's Semantic Kernel has been the bane of my existence at work — nonstandard abstractions, overengineered complexity, feature churn without clear direction or documentation, and lagging promises for feature parity across languages (Python, Java).
> These first-gen frameworks provided abstractions over the chat completion (call and response with LLM) but required complex handbuilt engineering for composition and orchestration; tool-use was an afterthought.
> "Second-gen" frameworks like LangGraph, CrewAI, and Pydantic AI treated "Agents" as the primary metaphor and improved modularity and composition (making the developer experience much nicer).
> These have since evolved into "Third-gen" SDKs for building Agent Harnesses, incorporating features like additional runtime support (retries, state, orchestration, tool use policies and governance, observability) and improved tools, context management, and memory.

Five frameworks surveyed in prose, because an organizing idea — three generations — does the work fragments can't; every tool gets a verdict with its reason, and the ranking lives in the verb choices.
The slop deletes the verbs; the near-miss restores them without deciding any fact's rank.
A genuine comparison matrix (N tools against the same columns) would still be a table; this is narration, so it is sentences.

## Documenting results — numbers first, caveats with teeth, interpretation labeled and last

Near-miss (hedge-smoothed, numbers buried):

> The analysis indicates that Omniscience Accuracy demonstrates relatively strong predictive performance, though it should be noted that the estimates carry a degree of uncertainty.
> It is also worth noting that knowledge-oriented benchmarks appear somewhat more predictive than task-oriented ones, which may suggest interesting implications for how parameter counts relate to capability.

Target:

> As mentioned in that podcast episode, Omniscience Accuracy indeed is the most predictive (R²=0.84), followed by MMLU Pro (R²=0.75) and trailed by the Intelligence Index (R²=0.07).
> (As a reminder, R² is a measure of how much total parameter variance the predictor(s) account for — a "goodness of fit" metric.)
> Their errors (mean absolute error (MAE) and root mean squared error (RMSE)) are generally around 200B total parameters — this is not a precise estimator!
> [...]
> I found it interesting that benchmarks that test _knowledge_ had the best fit, while benchmarks that test _task performance_ (Tau², GDPVal) were not predictive at all.
> This hints at parameter counts being innately tied to model knowledge capacity, while task performance is something that can be improved in post-training.

Findings arrive with their numbers attached; the limitation gets an exclamation, not a hedge; the speculation is labeled ("This hints at") and kept last.
In the source document the full metrics table stays a table — judgment in prose, lookup in structure.
The near-miss hedges every claim into "relatively," "somewhat," and "may suggest," and loses the numbers entirely.

## Recommending — personal stakes, a disposed objection, an imperative close

Near-miss (inflated stakes, no artifact):

> In the age of AI, safeguarding our cognitive sovereignty has never been more critical.
> Organizations and individuals alike must embrace intentional friction to ensure that human judgment remains at the center of the loop.
> The stakes could not be higher: our very capacity to think is on the line.

Target:

> The idea of losing my own cognitive sovereignty due to inattentive laziness terrifies me.
> _Idiocracy_ and _WALL-E_ are dystopian fables I'd prefer society does not realize.
> While model labs may never be incentivized to induce friction in their models or agents (surrendered users will increasingly need AI), inducing this intentional friction is quite simple — just tell the AI to make the user do the work (and why it matters).
> Most chatbots and coding agents support specifying custom user instructions.
> Unlike the prescribed protocols requiring individual discipline, a standing instruction is always active.
> The friction it induces does not depend on momentary motivation or care about external pressures to move faster.
> If you, like me, wish to resist cognitive surrender, drop this into your AI's instructions:

The stakes are personal and specific rather than civilizational; the objection is disposed of in a parenthetical; "quite simple" is paid off immediately by showing the simple thing; the close is an imperative that hands the reader the artifact.
The near-miss inflates the stakes to everyone and everything and ends before recommending anything actionable.

## Closing — concede, name the difficulty, admit the limit

Near-miss (the softened prophecy):

> The risks are real even if the policy fails.
> There is reason to expect the dynamics described here to hold through the coming decade as they have the past one, and the frameworks that take them seriously will be the ones that endure.

Target:

> _Do not let my rebuttal to the policies undermine the validity of the risk assessment._
> Examining these games makes it clear that the dynamics of strategic competition for AI dominance leads to an accelerating arms race; with this capability will come real threats.
> [...]
> Managing these risks is a Wicked Problem, requiring international cooperation that the current incentive structures do not support.
> Unfortunately, neither the authors nor I can offer a solution — until a clear and present danger emerges, AI will remain an accelerating, mostly unregulated field.

The closer concedes the opponent's strongest point, names the problem's actual difficulty class ("Wicked Problem" is a term of art, not decorative capitalization), and ends by admitting what the argument cannot deliver.
The near-miss is the residual that survives most de-slopping passes: the prophecy softened but intact.
Replace prophecy with the honest state of the world, a concrete next step, or a claim with a stated probability — never with a quieter version of destiny.

## Earned parallelism — the licensed triad

The tell (shape first, content absent):

> Training is easy.
> Scaling is harder.
> Alignment is hardest of all.

Target:

> It's easy to see how we got here — post-training suffers from a cold-start problem.
> Training next-token tasks is easy (self-supervised) and cheap (a single token gives a signal).
> Training call/response is harder (you need to train a reward model to assess response quality) and more expensive (you have to collect the data to train the reward model; you have to generate a complete response before you get a signal).
> Training over full conversations or agentic trajectories is even more complex and expensive (multi-turn data is rarer and harder to synthesize; long-horizon tasks require many responses before you get a signal).

Structurally a triad, licensed because the content is a real escalating cost gradient and every step carries its own reasons in parentheses.
Shape follows content.
If you find yourself building the shape first and hunting for three things to fill it, you are writing the tell.

## Developed analogy — introduce the mechanism before it explains anything

The tell (analogy asserted, asked to do the explaining by itself):

> Think of RLHF as a Pepsi Challenge: models are optimized for the sip, not the bottle.

Target:

> The Pepsi Challenge was (and is again) a blind taste test pitting Pepsi against Coca-Cola.
> Famously, participants favored Pepsi over Coke... but Coke has retained its larger market share despite marketing blunders (such as New Coke).
> The prevailing theory is that Pepsi is sweeter than Coke, and therefore preferred in blinded taste tests where only small sips are compared.
> When consuming larger amounts over longer periods of time, the sweetness that was initially preferred becomes cloying, leading to a longer-term preference for Coca-Cola.

The analogy receives a full paragraph of mechanism before it explains anything; the essay it comes from then reuses it as an analytic instrument — a preference leaderboard as a Pepsi Challenge, single-turn preference tuning as the small sip — and retires it before it wears out.
Introduced once, made to work, not repeated as decoration.
