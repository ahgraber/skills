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
  A conditional that a move's own verification requires, such as a constructor that rejects invalid combinations, is not a violation.
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

## Collapse mutually exclusive fields into one choice

Replace several fields, of which at most one is meaningful at a time, with a single field that holds one of a fixed set of alternatives.
Use an enum, a tagged union, or a sealed class hierarchy; where the language has none, use a single constructor function that rejects invalid combinations.

**Preconditions:** the invalid combinations the fields allow are known.
No stored or in-flight data contains an invalid combination.
The fields are not part of a serialized, persisted, or externally consumed format.
Collapsing such fields changes a contract and requires a migration plan, which this move does not include.

**Procedure:** define the new field.
Convert every site that creates a value.
Convert every site that reads one.
Locate read sites with the compiler, the tests, and a text search.
In a language without exhaustive matching, only the search finds all of them.
Delete the code that handled invalid combinations; removing that handling is the purpose of the move.
Delete the old fields.

**Verification:** invalid combinations cannot be constructed, or, where the language cannot enforce this, all construction passes through one function that rejects them.
The scattered checks for invalid combinations are gone.
The old fields are gone.
The test suite passes with the converted code exercised.

**Breaks behavior when:** an invalid combination was reachable in practice and something depended on how it was handled.
The old fields were written independently by a caller the search missed.
The fields turn out to be part of a serialized or stored format.

## Remove replicated information

Delete a field, column, or cache that holds information derivable from a source, and compute the value at the point of use.

**Preconditions:** the copy is required to equal its source at all times; every value of the copy is recomputable from the source; the cost of computing at read time is acceptable, or one cached accessor can hold the computation in a single place.
A copy that captures a value at a point in time, such as a price recorded at purchase, is a snapshot, and this move does not apply to it.

**Procedure:** locate every reader of the copy with the compiler, the tests, and a text search; include string-keyed access and access that supplies a default when the field is absent.
Replace each read with the computation from the source.
Then delete every write to the copy, then delete the field.
Convert reads first, because the remaining writes keep the copy correct during the conversion.
Delete the field last, because that turns any missed reader into an error.
A reader that tolerates a missing field produces no error; only the search finds it.

**Verification:** nothing writes the copy; every former reader computes from the source; no reader accesses the copy with a default fallback; stored records no longer carry the copy, or a migration is planned separately.

**Breaks behavior when:** the copy and the source had already drifted and behavior depended on the copy's value; a value of the copy is not recomputable from the source; a reader that tolerated the missing field was not found.
Compare copy and source on real data before deleting.
A disagreement means either a defect to fix first or a snapshot this move must not touch; determine which before proceeding.
