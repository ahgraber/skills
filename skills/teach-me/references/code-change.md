# The code-change branch

Mechanics for lessons whose subject is a specific code change — a diff, commit, range, branch, staged changes, or PR.
These steps replace guesswork with the actual change; skipping them produces a lesson about a change that doesn't exist.

## Resolve the change

Determine the exact diff to explain:

- **Staged changes** — `git diff --staged`.
- **A commit or range** — `git diff <range>` / `git show <sha>`.
- **A branch** — diff against its base, not against `HEAD` of the moment.
- **A PR** — the PR's merged diff (e.g. `gh pr diff <number>`), not the branch's latest state if they differ.

If the reference is ambiguous ("the change", "my PR"), ask which.
Read the full diff before writing anything.

## Explore the surrounding code — broadly

The diff alone is not enough context.
Read the files it touches and their neighbors, callers, and callees, so the Background section describes the system as it actually is.
This exploration is load-bearing; a shallow read produces a shallow lesson.

Questions the exploration must answer:

- What did the touched code do _before_ the change, and who depends on it?
- Why does the change take this shape — what constraint or convention in the surrounding code forced it?
- What does the change deliberately _not_ touch that a reader might expect it to?

## Section consequences

- **Background** orients the reader in the pre-change system — the part of the codebase the diff lands in.
- **Intuition**'s toy example uses the change's real inputs and outputs where possible: a real request body, an actual id, a sample payload.
- **Walkthrough** groups the edits by purpose and orders the groups so each builds on the last — never file-by-file in diff order.
- **Quiz** items test the change's purpose, mechanism, or behavior on new input — not trivia about the surrounding code.

## Boundaries

- Writing the commit message for the change — `commit-message`.
- Reviewing the change for bugs, security, or style — `code-review` or `securing-code`.
- Explaining a whole codebase or writing sustained library documentation — that is the codebase-area branch or `scaffold-docs`, not this one; the scope here is one change.
