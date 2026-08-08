# Structural Moves

Each move below preserves behavior only when its preconditions hold.
Check them while planning the move, before you start executing it.

## Verification: why a passing suite is weak evidence

A green suite after a move proves that the tests which ran still pass.
It does not prove the moved code ran at all.

Before you trust a green run:

- **Confirm the moved code is exercised.**
  Run the suite with coverage and check that the lines you moved are hit.
  Restructuring code that no test touches produces a green run that means nothing.
- **When coverage is thin, write a characterization test first.**
  Pin the current observable behavior, mapping inputs to outputs and including the ugly cases, then move.
  Write the safety net before you need it; it stays afterward as a regression guard.
- **Read your own diff for semantic tokens.**
  A behavior-preserving move will not introduce a new conditional, change a literal, reorder side effects, alter a default, or narrow an exception type.
  If the diff contains one of those, the move is either a mistake or something other than a refactor.
- **Compare the public surface.**
  Exported names, signatures, and defaults must match before and after, unless the plan said otherwise.

## Decompose a function

Split an oversized function into named parts.

**Preconditions:** the parts have identifiable responsibilities; extractable blocks do not share mutable local state in a way that forces passing five parameters back and forth.

**Procedure:** extract one block at a time, innermost or last-executed first.
Give each extraction a name describing what it produces rather than when it runs (`normalize_headers`, not `step_two`).
The original function becomes sequencing.

**Verification:** the caller-visible signature is unchanged; extracted parts are private unless the plan says otherwise; the suite covers the function.

**Breaks behavior when:** extraction changes when one side effect fires relative to another, or moves work across an exception boundary so a failure raises from a different place.

## Extract or move a module

Relocate code into a new or different module.

**Preconditions:** every importer is known and countable; the move creates no import cycle.

**Procedure:** move the definitions, update imports at every site, then check for stale re-exports left behind.
Leave a forwarding shim only when the module is public API and needs a deprecation path.
Do not add a shim for safety alone; one with no deprecation path is never removed.

**Verification:** no module imports the old location; the import graph is still acyclic; the suite is green.

## Collapse a layer

Remove indirection that forwards without deciding.

**Preconditions:** the layer has one implementation and no published extension point; no existing test uses it as a mock seam.
Check both while planning, because a mock boundary is a consumer.

**Procedure:** point callers at the underlying implementation, then delete the layer.
Where the layer renamed things, keep the underlying name rather than the wrapper's.

**Breaks behavior when:** the wrapper did something small you missed, such as a default, a type coercion, an ordering guarantee, or an exception translation.
Read it line by line before you delete it.

## Break an import cycle

**Preconditions:** you can name what each module actually needs from the other; the cycle is not load-bearing for a plugin registry.

**Procedure:** pick one of three approaches.
Extract the shared piece into a third module that both import, invert the dependency by defining the interface in the lower module, or move the one function that causes the cycle.
Prefer extraction, because it is the easiest to review.

**Verification:** the cycle is gone, no new cycle appeared, and import-time side effects still fire in a working order.
Deferred imports inside functions often mask a cycle, so check for those before you declare it broken.

## Split a class

Break a class doing several jobs into separate types.

**Preconditions:** the fields partition cleanly along the responsibilities; construction sites are known.

**Procedure:** identify field clusters and the methods that use each, extract the smaller responsibility first, then update construction sites.
If callers depend on the original type, keep it as a composition of the new ones.

**Breaks behavior when:** shared mutable state crosses the split and the two halves now hold separate copies.

## Invert a dependency

Fix a layering violation where a lower layer reaches upward.

**Preconditions:** the boundary the code must respect is stated somewhere, in a spec, a documented architecture, or a convention the rest of the tree follows.
Without that statement, this is a preference rather than a fix.

**Procedure:** define the contract in the lower layer, implement it in the upper, and inject at the composition root.

**Verification:** the lower layer no longer imports the upper; wiring exists exactly once.

## Rename across the tree

**Preconditions:** every reference is findable, including strings, config keys, serialized data, and documentation.
A reference the search missed breaks this move more often than any other.

**Procedure:** rename the definition, update references, then search again for the old name across all file types rather than source alone.
Check test fixtures and any persisted data that stores the name.

**Breaks behavior when:** the name appears in serialized output, an API response, an environment variable, or a database column.
Those are public surface, so renaming them is a behavior change that needs a migration path.

## Replace a data shape

Turn a dict-of-dicts or positional tuple into a named type.

**Preconditions:** the shape is stable and known; it does not cross a serialization boundary where the loose form is the contract.

**Procedure:** define the type, convert at the boundary where the data is created, then work outward to consumers.
Convert construction before access, so no code reads a half-converted shape.

**Breaks behavior when:** the old shape tolerated missing keys and the new type requires them, or iteration order mattered and the new type changes it.
