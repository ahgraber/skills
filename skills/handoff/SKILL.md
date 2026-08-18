---
name: handoff
description: |-
  Use when ongoing work or conversational context must continue in a new conversation, session, or agent with no shared history. Triggers: 'handoff', 'prepare context for next chat', 'summarize for a new session', 'continue this in another conversation'. Not for same-chat status updates or repository documentation.
---

# Handoff

Produce a transfer-ready handoff for in-progress work.

## Invocation Notice

- Inform the user when this skill is being invoked by name: `handoff`.

## Writing Style

Write the handoff in the voice of a professional technical writer.
Prefer ASD-STE100 Simplified Technical English: short sentences, one instruction per sentence, active voice, and one term per concept.
Keep identifiers, commands, paths, and file names exact.

## Critical Constraints

- Assume the recipient will see only the handoff document and nothing else.
- Output one fully filled handoff payload in chat.
- Do not create a handoff file unless explicitly requested.
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

## Workflow

1. Extract the objective, success criteria, and current status from available context.
2. Collect concrete evidence: files touched, commands run, validation status, blockers, and risks.
   - Include references that shaped the work — files read, URLs, specs, prior artifacts — not only files edited; give each a one-line note on what it holds and why the recipient needs it.
   - When a claim concerns repository state, verify it against the current working tree (`git status`, `git log`, `git diff --stat`) instead of conversation memory; the conversation's picture of the repo drifts over a long session.
   - Derive the Changes Made list from the diff itself (`git diff --stat`, plus `--cached` for staged work) and reconcile every changed file and notable hunk against it; conversation memory under-reports.
   - Report validation results only for checks run in this session; mark everything else as not run.
   - When the handoff content is conversational (ideation, decisions, drafts), the conversation itself is the source; skip repo verification.
3. Synthesize conversation-only content — decisions with rationale, user guidance, constraints, direction on drafts — so the recipient understands intent and tradeoffs.
   - Write it as a briefing for a new colleague: distill substance and intent; do not transcribe the conversation.
   - Quote exact wording only when the wording itself carries the value (user-authored text, names, error messages).
4. Determine continuation strictly:
   - Include only direction the user gave and the incomplete remainder of requested work.
   - If no continuation was established, ideate with the user what the next session should do before writing the handoff.
   - If the user gives no direction, omit the Continuation section; the startup prompt then tells the recipient to confirm direction with the user.
5. Fill every applicable section of `assets/handoff-template.md`; omit sections that do not apply per the template's markers.
6. When a Continuation section exists, order its items and make item 1 immediately executable.
7. Return the completed template in chat for copy/paste.

## Quality Checklist

- Section headings match the template exactly; repo-only and only-if-established sections are omitted when they do not apply.
- The goal and definition of done are explicit.
- Sections agree with each other; the Goal and Status lines do not contradict Pending or Validation.
- Done vs. pending work is unambiguous.
- Every open obligation appears in Pending or Continuation, not in a note or footnote.
- Every Continuation item traces to user direction or the remainder of requested work; no invented work.
- Changes Made covers every file in the diff; no change is omitted because it was forgotten.
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
