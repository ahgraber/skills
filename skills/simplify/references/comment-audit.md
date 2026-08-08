# Comment Audit

Comments are the part of a change that rots fastest, because nothing fails when they go wrong.
This lens keeps the ones carrying information the code cannot, fixes the ones that now lie, and deletes the rest.

## Scope: comments, not docstrings

**Docstrings are not comments.**
They are API surface, and the repo's linter and conventions govern their form.
A docstring restating parameter types can be required by the configured rules.
Read the repo's lint configuration before you touch one.

Docstrings are in scope for exactly one thing: **staleness**.
A docstring describing behavior the function no longer has is a defect, and it gets fixed the same way a stale comment does.
Their style, presence, and structure are the linter's business.

## The keep test

A comment earns its place when a competent reader of this codebase, reading the code carefully, would still get it wrong.

| Keep                                | What it covers                                                                            |
| ----------------------------------- | ----------------------------------------------------------------------------------------- |
| Why, where the why is not derivable | The constraint, invariant, or tradeoff behind the chosen approach                         |
| Gotchas                             | "This looks wrong but isn't", ordering that matters, a subtle cross-module interaction    |
| Workarounds                         | A platform quirk, an upstream bug, a version-specific behavior, with a link if one exists |
| Rationale for a non-obvious cost    | Why this is a loop instead of a comprehension, why this allocates                         |
| Citations                           | Algorithm sources, RFC or spec sections, issue links that explain the shape               |

## Delete

| Delete                      | Why                                                                            |
| --------------------------- | ------------------------------------------------------------------------------ |
| What-restatement            | A well-named identifier already carries it                                     |
| Change narration            | "Now we also handle X", "moved this up". True for one commit, misleading after |
| Point-in-time references    | The task, ticket, plan step, or conversation belongs in the commit message     |
| Commented-out code          | Version control already holds it                                               |
| Section banners             | ASCII dividers in a file that is already too long. The length is the finding   |
| Restatements of the obvious | "Increment the counter", "return the result"                                   |

The repo rule in [CLAUDE.md](../../../CLAUDE.md) states this for the code in this repository: comments describe what exists now, or why it is that way, and never what it used to be.
No "previously…", "no longer…", "changed from…", "renamed from…".
Delete stale historical asides on sight.

## Fix, do not delete

A comment that contradicts the code is worse than no comment, because a reader believes it.
Deleting it loses information; making it true keeps that information.

- If a comment describes behavior that changed, rewrite it to describe current behavior.
- If an example no longer runs or no longer produces the stated output, correct the example.
- If a comment references a renamed symbol, moved file, or deleted flag, update the reference.
- If a comment describes a constraint the code now enforces, delete it.
  The code says it.

If you cannot determine what the comment was trying to say, record that in the ledger instead of guessing or dropping it silently.

## Never touch

- License headers, copyright notices, SPDX identifiers
- Attribution and provenance comments
- Generated-file markers (`@generated`, "do not edit")
- Directives the toolchain reads: type-checker pragmas, linter suppressions, encoding declarations, editor config comments

A linter suppression that looks unnecessary is a separate finding.
Raise it; do not delete it as a comment.

## Defer to repo convention

Some comment questions have no universal answer.
Follow what the repository already does instead of importing a rule:

- **TODO, FIXME, HACK, XXX.**
  Whether these need an owner, a date, or an issue link is the repo's call, so match the surrounding convention.
  Flag a TODO whose stated condition has already been met.
- **Docstring style.**
  The linter decides.
- **Comment density.**
  Match the neighboring files.

## Signals this lens produces

A comment explaining a gotcha that no test covers is a **missing-test finding**, not a comment finding.
The comment is doing a test's job, warning a future reader about a failure mode that nothing will catch.
Keep the comment and record the gap in the ledger's Deferred section.
Writing that test is out of scope for a simplify pass.
