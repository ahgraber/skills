# Comment Audit

This lens keeps comments that carry non-derivable facts, rewrites stale comments that still carry them, and removes the rest.

## Scope: comments, not docstrings

**Docstrings are not comments.**
They have a separate content test.
Audit them with [docstring-audit.md](docstring-audit.md) and leave them alone here.

## The keep test

A comment earns its place when a competent reader of this codebase, reading the code carefully, would still get it wrong.

For every proposed edit, quote the comment and cite the code or external constraint that makes it redundant or stale.
If that evidence is unavailable, record a Tier 2 proposal.

| Keep                                | What it covers                                                                            |
| ----------------------------------- | ----------------------------------------------------------------------------------------- |
| Why, where the why is not derivable | The constraint, invariant, or tradeoff behind the chosen approach                         |
| Gotchas                             | "This looks wrong but isn't", ordering that matters, a subtle cross-module interaction    |
| Workarounds                         | A platform quirk, an upstream bug, a version-specific behavior, with a link if one exists |
| Rationale for a non-obvious cost    | Why this is a loop instead of a comprehension, why this allocates                         |
| Citations                           | Algorithm sources, RFC or spec sections, issue links that explain the shape               |

Before retaining a workaround, check that its platform, supported version, or upstream issue still applies.
If that evidence is unavailable, record a Tier 2 proposal.

## Delete

| Delete                      | Why                                                                            |
| --------------------------- | ------------------------------------------------------------------------------ |
| What-restatement            | A well-named identifier already carries it                                     |
| Change narration            | "Now we also handle X", "moved this up". True for one commit, misleading after |
| Point-in-time references    | A task, plan, or change-history reference belongs in the commit message        |
| Commented-out code          | An obsolete source copy belongs in version control                             |
| Section banners             | Decorative dividers that do not label a code region                            |
| Restatements of the obvious | "Increment the counter", "return the result"                                   |

Follow the target repository's convention for historical comments.
When it prohibits them, delete stale historical asides after confirming they do not document a live migration or workaround.
Confirm that commented-out code is not a template, migration procedure, or documentation example before deleting it.
Do not delete a section banner because a file is long.
Record an overlong file as a separate Tier 2 refactor observation; it does not resolve or justify a banner-deletion finding.

## Fix when content remains

A comment that contradicts the code is worse than no comment, because a reader believes it.
Rewrite it only when it carries a fact that the reader still needs.

- Rewrite a stale behavior description, example, or reference only when the revised comment states a non-derivable current fact.
  Otherwise, delete it.
- Delete a constraint comment only when the code or an authoritative source makes both the constraint and its rationale clear.
- Keep a live issue link when it establishes a current workaround or removal condition.

If you cannot determine what the comment was trying to say, record a Tier 2 proposal instead of guessing or dropping it silently.

## Before editing, find who reads it

Check comments that contain examples, documentation markers, or text a tool can render or execute.
Doctests, documentation generators, and language-specific API documentation comments can consume them.
If a tool or test consumes the target comment, treat the edit as Tier 2 unless the configured check proves preservation.

## Never touch

- License headers, copyright notices, SPDX identifiers
- Attribution and provenance comments
- Generated-file markers (`@generated`, "do not edit")
- Directives the toolchain reads: type-checker pragmas, linter suppressions, encoding declarations, editor config comments

Do not assess toolchain directives in this lens.
Use configured tool output for unused suppressions.

## Defer to repo convention

Some comment questions have no universal answer.
Follow what the repository already does instead of importing a rule:

- **TODO, FIXME, HACK, XXX.**
  Whether these need an owner, a date, or an issue link is the repo's call, so match the surrounding convention.
  Flag a TODO only when code or an authoritative source proves its stated condition has been met.
- **Comment density.**
  Match the neighboring files.

## Signals this lens produces

When a comment describes a behaviorally testable invariant and evidence establishes an uncovered gap, keep the comment and record a missing-test observation in the ledger for `code-review`.
Do not infer absent coverage from a quick search.
