---
name: commit-message
description: |-
  Use whenever a Conventional Commit message is being drafted — whether the user asks ("write commit message", "draft commit from staged changes", "generate conventional commit", "message for git commit -F -") or you are about to propose one proactively after finishing work (e.g. completing tasks, wrapping up a feature, or summarizing staged changes). Invoke before writing the message inline. Not for creating commits, amending history, or full code review.
---

# Commit Message

Draft a Conventional Commit message from staged changes.

## Invocation Notice

- Inform the user when this skill is being invoked by name: `commit-message`.

## Critical Constraints

- Use only staged changes (`--cached` / staged SCM state) as input, unless the user invokes the **Context Override** path.
- Resolve and use the repository root for all SCM calls.
- If no staged changes exist after one retry, stop and inform the user (standard workflow only).
- Always include an `AI-assistant: <AGENT>` footer.
- Output only the final commit message in one markdown code block.
- Body content: apply **Body Discipline** (below) at draft time, not as an afterthought.

## Body Discipline

These rules govern body content.
Apply them at draft time (step 7) and re-check before output (step 9).

### Cold-reader test

Your reader meets this commit in two phases: **Scan mode** — they see the subject in `git log`, `git blame`, or a bisect and decide whether to open it.
**Read mode** — once opened, they read the diff to understand what changed.

The **subject** carries scan mode — name the area and effect concretely enough to distinguish from neighbors.

The **body** exists only when read mode leaves a question unanswered.
If no gap exists, ship subject-only — most commits.
Conversation weight is not reader weight: what felt load-bearing in the dialogue is rarely what the diff fails to convey.

The diff shows what changed and where, but not why or how to act on it.
A body line is warranted only when it fires one of these **5 triggers**:

1. **Why this choice** — when the subject names a choice but not the constraint that forced it.
2. **Tuning rationale** — magic numbers, thresholds, or tunables a future reader will want to revisit.
3. **Wrong-fix guards** — foreseeable "fixes" that would re-break the change.
4. **Cross-cutting impact** — callers, consumers, or schema implications the diff doesn't reach.
5. **External references** — issues, advisories, RFCs.

### Trigger-naming rule

For every body line you are about to write, name which of the 5 cold-reader triggers it fires.
If you can't name one, don't write the line — it's conversation weight or file inventory, not reader signal.
"It feels useful to mention" is not a trigger.

### Brevity gate

Could the subject alone carry this commit?
Drop the body entirely.
Does any body line restate the subject?
Drop it.

### Line-level filters

- Names an internal symbol → restate as the public-surface description.
- Describes how, not what → restate as outcome.
- Inventories file contents (line counts, lists of topics covered, lists of items the file enumerates) → drop, the diff already shows this.
- Bookkeeping (file moves, archive, sync, lockfile) → drop unless the reader needs to act.

## Workflow

01. Check for a context override.
    If the user directs you to draft from prior conversation work or a working document (e.g. "use what we just did", "based on the todo list above", "from our discussion", "skip the diff"), follow the **Context Override** path below instead of the rest of this workflow.

02. Resolve repository root.
    Prefer workspace root when known; otherwise run `git rev-parse --show-toplevel`.

03. Retrieve staged changes.
    Prefer `get_changed_files` with `repositoryPath: <repo-root>` and staged state.
    If that tool is unavailable, use SCM tooling with explicit repo context.
    If SCM tooling is unavailable, use `git -C <repo-root> diff --cached`.

04. Validate staged content exists.
    If empty, retry once with explicit repo root; if still empty, inform user and stop.

05. Analyze the staged diff.
    Identify changed files, behavior impact, logical scope, and likely commit type.

06. Incorporate user arguments/context when provided.
    Preserve explicit issue refs and constraints from user input.

07. Apply the **Cold-reader test** and **Trigger-naming rule** (see § Body Discipline) to decide whether the body is warranted and which lines to write.

08. Read `references/conventional-commit-rules.md`.
    Then draft the message covering only the lines named in step 7, applying those rules.

09. Self-check before returning, in order:

    - **Brevity gate** (see § Body Discipline)
    - **Cold-reader test** — re-apply the **Trigger-naming rule** to each remaining body line; drop any line that fires no trigger
    - **Line-level filters** (see § Body Discipline)

    Revise or drop any failing lines before output.

10. Return only the final message in a fenced code block, ready for `git commit -F -`.

## Context Override

Use this path when the user explicitly directs you to draft from prior conversation work or a working document rather than from the staged diff.
**Body Discipline applies here too** — conversation-derived drafts are the highest-risk source for conversation weight.

1. Identify the source the user pointed to: prior turns in this conversation, a referenced todo list, a plan, a handoff note, or another working document.

2. Extract the scope, intent, and behavior changes from that source.
   Do not run `git diff`, `get_changed_files`, or any other SCM inspection.

3. If the source is ambiguous or insufficient (no clear scope, type, or "what changed"), ask the user one targeted clarifying question or fall back to the standard workflow — do not invent details.

4. Apply the **Cold-reader test** and **Trigger-naming rule** (see § Body Discipline) to decide whether the body is warranted and which lines to write.

5. Read `references/conventional-commit-rules.md`.
   Then draft the message, preserving any explicit issue refs and constraints the user provided.

6. Self-check before returning, in order:

   - **Brevity gate** (see § Body Discipline)
   - **Cold-reader test** — re-apply the **Trigger-naming rule** to each remaining body line; drop any line that fires no trigger
   - **Line-level filters** (see § Body Discipline)

7. Return only the final message in a fenced code block, ready for `git commit -F -`.

## References

- `references/conventional-commit-rules.md` - subject/body/footer rules and examples.
