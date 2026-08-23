# Data Representation

Audit data structures for designs that invite unforced errors.
The audit runs three tests: invalid states, replicated information, and extension cost.
Apply it to whatever scope is given: a diff, a file, or a codebase.
Report findings with evidence; decide what to change in triage with the user.

Tests may not catch these failures.
They demonstrate that the schema can model the states the author had in mind, but they do not validate whether the schema itself is poorly designed.
Run the audit as a deliberate pass, not as a byproduct of a correctness review.

## Where to look

Audit the structures that cross a boundary first.
A boundary is any place where the code that produces data and the code that consumes it cannot be changed together: a module's public interface, an API request or response, a stored record, a queued message, a file format, output another team reads.
A shape that stays inside one function can be fixed in one edit.
A shape that has crossed a boundary is a contract, and fixing it later is a migration.
The `python` skill's `references/design-boundaries.md` describes the same boundaries from the design side.

For a diff, audit every structure the change adds or grows, and every field the change adds beside an existing structure rather than into it.
For a file or codebase, order the structures by the boundary rule and state which structures were not examined.

## Test 1 — Invalid states

An invalid state is a state the domain does not allow.
Determine whether the structure can represent one.
Apply this test to boundary-crossing structures first.
Derive domain rules from the specification, then tests, then comments, then usage, in that order.
Label any rule inferred from usage as inferred in the finding.
A structure that can represent an invalid state transfers enforcement to its consumers, as guard code or as unchecked assumptions.
Existing guard code is evidence for the finding, never a reason to omit it.
Judge representability by the declared shape under ordinary use of the structure.
Ignore states reachable only through mutations the language permits but ordinary use does not perform.
Do not flag a shape that is the agreed contract at an external boundary.
Do not flag a value set that is intentionally open.
Record in each finding an invalid state the structure accepts and the operations that produce it.

## Test 2 — Replicated information

Find information stored in more than one place.
Do not audit the codebase for replication at large: start from each structure in scope and follow its information to the places it is written, sent, or received.
A place includes a field on another type, a database column paired with an in-memory field, a message payload paired with a receiver's store, and the same quantity expressed in two units.
For each set of copies, determine what keeps them in agreement, and name it in the finding.
Structural agreement means one copy is computed from the other, or one write updates all copies; do not report it.
Manual agreement means updates to each copy are separate operations; a missed update produces copies that disagree, and reads then return different values depending on which copy is consulted.
Intentional divergence means the copy captures a value at a point in time, such as a price at purchase, and is meant to stop tracking its source.
Report manual agreement and intentional divergence; triage with the user decides whether each is acceptable.
For each finding, supply as evidence the copies and a sequence of ordinary operations after which they disagree; for intentional divergence, the sequence shows the divergence is intended.

## Test 3 — Extension cost

This test measures the cost of extending the structure with a new case: a new state, variant, or kind.
Apply this test to boundary-crossing structures first; their consumers are the most numerous and the least able to change together.
Propose a realistic extension.
Identify every edit site that must change to handle the new case.
Determine how each edit site would be discovered.
The possible discovery mechanisms are a compiler error, a failing test that iterates the structure's cases, a single dispatch point that routes all cases, and a text search.
Report a finding when an edit site is discoverable only by text search.
The number of edit sites is not the criterion.
An edit site missed during an extension continues to run and handles the new case incorrectly, without an error.
In a language without exhaustiveness checking, search-only discovery is the default, so the criterion becomes the absence of any mechanism that enumerates the cases: a dispatch table, a registry, or a test that iterates the cases.
As evidence for each finding, record the proposed extension, the edit sites, and the discovery mechanism for each edit site.

## Evidence

Each test states the evidence its findings require.
A finding without that evidence is an opinion; do not report it.

## Suggesting the fix

Say what shape would remove the failure, and stop there.
Changing a data structure touches every consumer, so the fix is rarely applied during the audit.
The `refactor` skill's `references/structural-moves.md` covers carrying out this kind of change safely.
