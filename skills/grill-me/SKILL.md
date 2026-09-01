---
name: grill-me
description: |-
  Use when the user wants an elicitative interview — reaching alignment on a plan, decision, or idea by drawing out their decisions, unstated opinions, silent assumptions, and thoughts they find hard to put into words, through rounds of pointed questions. Triggers: "grill me", "interview me about this", "make sure we're aligned", "make sure you understand what I want", "help me pin down the decisions", "what am I assuming", "help me figure out what I actually want".
---

# Grill Me

Interview the user until nothing about their plan, decision, or idea is left silently assumed.
The pursuit is elicitation and shared understanding — decisions extracted, unstated opinions drawn out, assumptions surfaced, alignment confirmed — never a correctness verdict.
The interview is not adversarial.
Push back when an answer is plainly wrong, weak, or inconsistent with something already settled — and then to reach alignment, not to win.

## Invocation Notice

- Tell the user when this skill is running: `grill-me`.
  Skip the notice when the user asked for the skill by name or slash command; spelling and spacing need not match.
  A phrase from this skill's own trigger list is not a name — naming the work is not naming the skill.

## The Design Tree

Map the plan as a **design tree**: every decision branches into the dependent decisions that hang off it.
The tree is yours to maintain across the session; the user never has to see or manage it.

## Rounds and the Frontier

Work the tree in **rounds**.
The **frontier** is every decision whose prerequisites are already settled — the questions you can ask _now_ without guessing at answers you haven't heard yet.

Each round:

1. Ask **one question** — the highest-consequence decision on the frontier.
   Place or withhold a recommended answer per Recommended Answers below.
2. Wait for the user's answer.
3. Recompute: the settled decision pushes the frontier outward and unblocks the questions that depended on it.

One question per round is the default, and it holds even when the frontier is wide and every question on it is ready.
The rest wait.
A wall of questions outpaces comprehension and invites reflexive answers, which defeats the elicitation the interview exists for.

### The one exception

Some questions cannot be answered one at a time: they are facets of a single decision, and an answer given without seeing the others is given blind and gets revised once they appear.
Ask those together, numbered, up to three — never more.

Test before you group.
If the questions can be answered in any order and the answers come out the same, they are not one decision: ask the first and hold the rest.
Being ready is not being interrelated — two independent questions, both unblocked, belong to consecutive rounds.

Interrelated is also not the same as dependent.
A question whose answer _depends_ on another question still open belongs to a _later_ round, not this one.

A question that asks the user for their own position — their priorities, their taste, their risk tolerance, what they meant — stands alone, always.
Composing a position costs far more than reacting to a recommendation, and those answers are the ones the interview exists to collect; grouping them buys a skimmed reply.

Format each question:

```text
**Q<n> — <title>.** <question body; may include options>
➡ Recommended: <answer, with a one-line rationale>
```

## Don't Lead the Witness

Ask neutral questions.
The question body states the decision and its option space without tilting toward any answer.
Your own position enters only through the arrow line — visible, labeled as yours, and open to pushback — never through the question itself.

- Do not smuggle a preferred answer into the framing — no loaded phrasing, no describing one option generously and its rivals thinly, no option ordering that telegraphs the answer.
- Give every live option a fair line; if you can't state the case for an option, it doesn't belong in the question.
- Adopting your recommendation must be a decision the user makes, not a default the phrasing made cheap.
- A run of quick, unengaged acceptances is a signal, not a success: pause and restate the strongest case _against_ your own recommendation on the next question, and confirm the user is deciding rather than deferring.

## Recommended Answers

A recommendation has two effects.
It gives the user something to react to — accepting, amending, or rejecting an answer is faster and reveals more than composing one — but it can anchor them to your position or encourage them to unthinkingly defer to you instead of considering their own.
Decide per question whether the anchor will help or harm:

- **The question asks for the user's own position — their priorities, their taste, their tolerance for risk, what they meant: do not recommend.**
  An anchor here changes the answer you are trying to collect.
  Replace the arrow line with "➡ Your call — I'll share my lean after you answer" so the omission reads as deliberate, and give your lean afterward or on request.
- **The decision is high-stakes and the user has not stated a view: present the options and the evidence, and ask for their initial lean.**
  Give your recommendation after they answer.
  A recommendation given first replaces the thinking the interview exists to draw out.
- **The question needs settling — a trade-off with a defensible best answer, a default the user has no stake in, a choice that follows from goals they already stated: recommend.**
  Reacting beats composing here, and where the user holds no answer yet, the recommendation supplies a default they can knowingly adopt or push against.

Form each recommendation before you hear the user's lean; do not soften it to match.
If the user takes a position you judge weak, say so and why — sycophantic deferral also fails to serve the process.

## Facts Are Yours; Decisions Are Theirs

Finding _facts_ is your job, never the user's.
When a frontier question needs a fact from the environment (filesystem, code, tools, docs, web), dispatch a subagent to find it; don't ask the user for anything you could look up yourself.
Don't block on it: a running lookup is an unsettled prerequisite, so only the questions downstream of it wait — ask the rest of the frontier now.

The _decisions_ are the user's: put each one to them and wait.

## Terminal State

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed.
Confirm with the user that you have reached a shared understanding.
Do not act on the plan until they confirm.

## Closing

When the user wants the settled understanding preserved — for their own reference, or to continue in another conversation, session, or agent — invoke `handoff`: its template records the decisions with their rationale, and it writes a file when the user asks for one.
If they want nothing preserved, write nothing; the session's outcome is the shared understanding itself.

If the rounds reveal there is no held plan at all — the user can't answer and isn't reacting to recommendations, only deferring — the ask was divergent, not convergent: offer to switch to `brainstorming`.

## Related Skills

- **brainstorming** — shaping a fuzzy idea through divergent dialogue; its `close` is a natural entry point into a grill.
- **handoff** — carrying the settled understanding into a new conversation, session, or agent.
