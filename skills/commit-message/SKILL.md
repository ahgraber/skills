---
name: commit-message
description: |-
  Use when drafting a Conventional Commit message from currently staged Git changes. Triggers: 'write commit message', 'draft commit from staged changes', 'generate conventional commit', 'message for git commit -F -'. Not for creating commits, amending history, or full code review.
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

## Workflow

1. Check for a context override.
   If the user directs you to draft from prior conversation work or a working document (e.g. "use what we just did", "based on the todo list above", "from our discussion", "skip the diff"), follow the **Context Override** path below instead of steps 2-7.
2. Resolve repository root.
   Prefer workspace root when known; otherwise run `git rev-parse --show-toplevel`.
3. Retrieve staged changes.
   Prefer `get_changed_files` with `repositoryPath: <repo-root>` and staged state.
   If that tool is unavailable, use SCM tooling with explicit repo context.
   If SCM tooling is unavailable, use `git -C <repo-root> diff --cached`.
4. Validate staged content exists.
   If empty, retry once with explicit repo root; if still empty, inform user and stop.
5. Analyze the staged diff.
   Identify changed files, behavior impact, logical scope, and likely commit type.
6. Incorporate user arguments/context when provided.
   Preserve explicit issue refs and constraints from user input.
7. Draft the commit message using `references/conventional-commit-rules.md`.
8. Return only the final message in a fenced code block, ready for `git commit -F -`.

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
