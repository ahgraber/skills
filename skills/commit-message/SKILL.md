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
- Body content rules (apply at draft time, not as an afterthought):
  - State outcomes the reader can act on, not mechanisms.
  - Don't name internal symbols (private helpers, parameter lists); name the public surface that changed.
  - Internal-only refactors collapse to one phrase or are omitted.
  - Drop bookkeeping (file moves, archive operations, sync steps).

## Workflow

01. Check for a context override.
    If the user directs you to draft from prior conversation work or a working document (e.g. "use what we just did", "based on the todo list above", "from our discussion", "skip the diff"), follow the **Context Override** path below instead of steps 2-8.

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

07. Frame for the future reader before drafting.
    Conversation weight is not reader weight — what felt load-bearing in dialogue is rarely what a cold reader needs.
    Name three things, in order:

    1. **What changed** at the behavior or system level (not "modified function X" — that's diff-level).
    2. **Why** — the motivation, even when it's a single phrase.
    3. **0-3 things a future maintainer would otherwise miss** — non-obvious rationale, tuning assumptions, foreseeable wrong "fixes" to guard against.
       If empty and #2 is implied by the subject, ship subject-only.

08. Read `references/conventional-commit-rules.md`.
    Then draft the message covering only the items named in step 7, applying those rules.

09. Self-check before returning.
    For each line in the body, verify:

    - Does it name an internal symbol?
      If yes, drop or replace with the public-surface description.
    - Does it describe how, not what changed?
      If yes, restate as outcome.
    - Is it bookkeeping (file moves, archive, sync, lockfile)?
      If yes, drop unless the reader needs to act on it.
    - Is it a recap of a decision made in conversation that didn't shape the code?
      If yes, drop.
      Revise any failing lines before output.

10. Return only the final message in a fenced code block, ready for `git commit -F -`.

## Context Override

Use this path when the user explicitly directs you to draft from prior conversation work or a working document rather than from the staged diff.

1. Identify the source the user pointed to: prior turns in this conversation, a referenced todo list, a plan, a handoff note, or another working document.
2. Extract the scope, intent, and behavior changes from that source.
   Do not run `git diff`, `get_changed_files`, or any other SCM inspection.
3. If the source is ambiguous or insufficient (no clear scope, type, or "what changed"), ask the user one targeted clarifying question or fall back to the standard workflow — do not invent details.
4. Draft the commit message using `references/conventional-commit-rules.md`, preserving any explicit issue refs and constraints the user provided.
5. Return only the final message in a fenced code block, ready for `git commit -F -`.

## References

- `references/conventional-commit-rules.md` - subject/body/footer rules and examples.
