---
name: handoff
description: |-
  Use when ongoing work or conversational context must continue in a new conversation, session, or agent with no shared history. Triggers: 'handoff', 'prepare context for next chat', 'summarize for a new session', 'continue this in another conversation'. Not for same-chat status updates or repository documentation.
---

# Handoff

Produce a transfer-ready handoff for in-progress work.

## Writing Style

Write the handoff in the voice of a professional technical writer.
Prefer ASD-STE100 Simplified Technical English: short sentences, one instruction per sentence, active voice, and one term per concept.
Keep identifiers, commands, paths, and file names exact.

## Fidelity by Type

Compress by item type, not at one uniform rate.
Summarize a rule and it may no longer state the rule.
Summarize a narrative and nothing important is lost.

- Constraints and procedures: record verbatim, and name the source.
- Decisions, rationale, preferences, and open questions: compress to the substance and the reason.
- Session narrative: drop it and record the end state instead.

A constraint is any rule that limits or directs the work: a prohibition, a required tool or command, a fixed format or output shape, a threshold, an ordering requirement.
Imperative wording is easy to find: "never edit the lockfile".
Declarative wording is harder and is lost more often: "this repo signs commits with the agent key", "the endpoint rejects payloads over 4 MB".
Record both.

The Session Constraints section of the handoff is a record of what this session operated under.
It does not instruct the recipient, who may be reading for context and not continuing the work.
Attribute each constraint so the recipient can tell a live user instruction from one the session inherited.

When this session started from an earlier handoff, copy that handoff's constraints forward word for word and mark them as coming from it.
Do not re-summarize a constraint an earlier handoff already recorded verbatim.
Each round of paraphrase drops more of the wording, and handoffs chain.

When one body of work is split across several handoffs, repeat each constraint in every handoff whose work it covers.

## Critical Constraints

- Assume the recipient will see only the handoff document and nothing else.
- Output one fully filled handoff payload in chat.
- Write it to a file only when the user asks for one; a request already made — including accepting another skill's offer to save — counts, so do not ask again.
- Do not rely on references like "above" or "earlier in this thread"; carry the substance of conversation-only information into the handoff itself.
- Record, do not decide: every statement must trace to the user's words, the session's actions, or an artifact.
  Do not infer next actions, select new work, or extend scope.
- If information is missing, write `Unknown` and specify what is needed.
- If a section genuinely has no items, write `None` — `None` and `Unknown` are different claims.
- Omit sections marked repo-only in the template when no repository is involved or repo state is irrelevant to the work.
- Omit sections marked only-if-established when the session produced nothing for them; never invent content to fill a template slot.

## Failure Modes

- Optimistic closure: reporting work as done when its evidence (file, commit, passing check) does not exist.
  Verify before claiming.
- Journey narration: recording the session chronologically ("first I tried…").
  Record the end state: artifacts, decisions, unresolved items.
- Slot-filling: inventing next steps or open questions because the template has a heading for them.
  An omitted section can be a correct answer.
- Uniform compression: paraphrasing a constraint at the same rate as narrative.
  The paraphrase reads well and no longer states the rule.

## When to Use

- Handing off work to a new conversation or agent.
- Resetting context while preserving execution continuity.
- Transferring partially complete implementation/debugging work.
- Transferring ideation, research, or writing context that lives only in the conversation.
- Capturing next actions before ending a session.

## When Not to Use

- Simple same-thread progress updates.
- Creating long-lived project documentation.
- Retrospectives not intended for immediate continuation.

## Invocation Notice

- Tell the user when this skill is running: `handoff`.
  Skip the notice when the user asked for the skill by name or slash command; spelling and spacing need not match.
  A phrase from this skill's own trigger list is not a name — naming the work is not naming the skill.

## Workflow

1. Extract the objective, success criteria, and current status from available context.
2. Collect concrete evidence: files touched, commands run, validation status, blockers, and risks.
   - Include references that shaped the work — files read, URLs, specs, prior artifacts — not only files edited; give each a one-line note on what it holds and why the recipient needs it.
   - When a claim concerns repository state, verify it against the current working tree (`git status`, `git log`, `git diff --stat`) instead of conversation memory; the conversation's picture of the repo drifts over a long session.
   - Derive the Changes Made list from the diff itself (`git diff --stat`, plus `--cached` for staged work) and reconcile every changed file and notable hunk against it; conversation memory under-reports.
   - Report validation results only for checks run in this session; mark everything else as not run.
   - When the handoff content is conversational (ideation, decisions, drafts), the conversation itself is the source; skip repo verification.
3. Collect the constraints the session operated under and record each one verbatim.
   - Cover instructions from the user, rules from repository or project documents the session followed, and constraints from an earlier handoff this session started from.
   - Read for declarative wording as well as imperative wording; see Fidelity by Type.
4. Synthesize the remaining conversation-only content — decisions with rationale, direction on drafts — so the recipient understands intent and tradeoffs.
   - Write it as a briefing for a new colleague: distill substance and intent; do not transcribe the conversation.
   - Quote exact wording when the wording itself carries the value (user-authored text, names, error messages).
5. Determine continuation strictly:
   - Include only direction the user gave and the incomplete remainder of requested work.
   - If no continuation was established, ideate with the user what the next session should do before writing the handoff.
   - If the user gives no direction, omit the Continuation section; the startup prompt then tells the recipient to confirm direction with the user.
6. Fill every applicable section of `assets/handoff-template.md`; omit sections that do not apply per the template's markers.
7. When a Continuation section exists, order its items and make item 1 immediately executable.
8. Check the constraints from step 3 one by one against the finished Session Constraints section.
   Restore any that the draft dropped or paraphrased.
   If one cannot be recorded, say so in the document; do not drop it silently.
9. Return the completed template in chat for copy/paste.

## Quality Checklist

- Section headings match the template exactly; repo-only and only-if-established sections are omitted when they do not apply.
- The goal and definition of done are explicit.
- Sections agree with each other; the Goal and Status lines do not contradict Pending or Validation.
- Done vs. pending work is unambiguous.
- Every open obligation appears in Pending or Continuation, not in a note or footnote.
- Every Continuation item traces to user direction or the remainder of requested work; no invented work.
- Changes Made covers every file in the diff; no change is omitted because it was forgotten.
- Session Constraints holds every rule the session operated under, quoted, each with its source.
- Constraints taken from an earlier handoff are copied word for word, not re-summarized.
- References list only sources actually consulted, each with why it matters; no padding with plausible links.
- Statements are specific and verifiable; no vague summaries.
- Validation status includes what passed, failed, or was not run (when checks apply).
- Blockers include dependency/owner and concrete impact.
- When a Continuation section exists, its first item can be executed immediately.
- A continuation item that runs a check names its expected result and what to do if it fails.
- Command results stay on one line with inline code; no fenced code blocks nested inside the template's outer fence.
- The recipient can proceed, or knows exactly what to ask the user, without reconstructing lost context.

## References

- `assets/handoff-template.md` - canonical output format.
