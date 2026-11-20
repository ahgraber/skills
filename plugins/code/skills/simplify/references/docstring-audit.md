# Docstring Audit

Docstrings can surface in editor hover, `help()`, and generated API docs without the reader opening the body.
That makes their content a separate concern from `comment-audit.md`.

## Scope: content, not form

This lens does not decide whether a docstring must exist, which convention it follows, or whether it lists every parameter.
Read linter configuration for docstring presence and format rules, test configuration for doctest and snapshot collection, and documentation or CLI configuration for docstring consumers.

This lens reviews whether an existing docstring describes the contract rather than the implementation, and whether evidence shows it is false.

## The caller test

**A docstring states what a caller must know to use the thing correctly without opening the body, and nothing that only makes sense while looking at the body.**

This is a two-sided test, unlike the comment keep test.
A comment has only a floor — earn your space.
A configured lint rule or repository convention can set a docstring's floor.
The caller contract sets its ceiling and bars implementation leakage.

The caller test decides whether a sentence narrates the body:

> **Would this sentence become false after a body rewrite that preserves the caller contract, including documented performance guarantees?**
> If yes, it narrates the body.
> Cut or salvage it.

A refactoring preserves the caller contract, so its docstring must remain true after that refactoring.
"Builds a dict from a loop" narrates a mechanism.
"Returns entries indexed by ID" states a result.

Names absent from the signature are a leakage signal only when they are locals or undocumented private implementation details.
An environment variable, protocol header, configuration file, or related public symbol can be part of the contract.

Every finding must quote the target sentence and identify the relevant contract or implementation detail.

## Keep

| Keep                              | Because the caller cannot get it from the signature                                       |
| --------------------------------- | ----------------------------------------------------------------------------------------- |
| The effect, in the caller's terms | What is true after the call that was not true before                                      |
| Contract not encoded in types     | Units, ranges, valid argument combinations, ordering guarantees, encoding, timezone       |
| Return semantics                  | Empty list vs. `None` vs. raise; whether the result aliases an argument or is a live view |
| Failure modes                     | Which exceptions, under which caller-visible condition                                    |
| Side effects                      | Mutates an argument, writes to disk, hits the network, acquires a lock, spends money      |
| Usage constraints                 | Must call `connect()` first, unsafe after `close()`, not thread-safe, single-use iterator |
| Surprising cost                   | A round trip per element, quadratic in the input, loads the whole file into memory        |
| Choice guidance                   | When to call this rather than the similarly named neighbor                                |

## Cut

| Cut                                     | Where it belongs                                              |
| --------------------------------------- | ------------------------------------------------------------- |
| Body narration                          | Nowhere. The body says it                                     |
| Type and name restated without meaning  | Nowhere. `name: str` already said it                          |
| Algorithm or data structure choice      | A body comment when no caller-visible guarantee depends on it |
| Private helpers and internal names      | Nowhere in public docstrings                                  |
| Rationale for the implementation        | A body comment, at the line that needs defending              |
| Change history, tickets, TODOs          | Commit message and issue tracker                              |
| The class docstring repeated per method | The class docstring                                           |

## Salvage before you cut

Narration sometimes has a contract fact buried in it.
"Loops over the items in insertion order and yields each one" is narration wrapped around a guarantee a caller can depend on.
Promote it — "Yields items in insertion order" — rather than deleting the sentence whole.
This rule is what keeps an audit from destroying information while removing noise.

## Fix, do not delete

A docstring that contradicts established behavior is worse than none, because a reader can act on it.
Rewrite a stale contract clause when the object still needs it.
Do not invent a contract merely to retain a docstring.
When cutting would empty a docstring, record a Tier 2 removal proposal.

- Rewrite a summary line that describes behavior the function no longer has.
- Delete a documented parameter that no longer exists.
  An undocumented parameter is a coverage question outside this lens; a configured rule can report it.
- Correct a `Returns` or `Raises` section only when a test, specification, or exercised behavior establishes the contradiction.
- Correct an `Examples` block whose stated output is wrong.
  Doctests and other test or documentation tooling can execute those blocks.
- Update a reference to a renamed symbol, moved module, or deleted flag.

## Before editing, identify how text is used

A docstring can be executable test input or product output, so identify the concrete consumer before treating an edit as Tier 1:

- **Tests.**
  Doctests, snapshot tests, and documentation builds that diff generated output execute or assert on the text.
  Treat the edit as Tier 2.
- **CLI frameworks.**
  Several render `__doc__` as command help, so the edit changes product copy.
  Treat the edit as Tier 2.
- **API documentation.** `help()`, editor hover, and generated reference pages render the docstring as API documentation.
  Do not treat that rendering alone as a Tier 2 consumer.
- **Runtime reads of `__doc__`.**
  Treat a direct read as Tier 2 only when it executes or asserts on the text, or renders product output.

Use Tier 2 only for a concrete consumer that matches one of those conditions.

## Where the test bends

- **Classes.**
  What the object represents, its invariants, its lifecycle, its thread-safety.
  Not an inventory of the methods; the reader already has that list.
- **`__init__`.**
  What makes an instance valid, and what construction does beyond assignment.
- **Properties.**
  What the value means and whether reading it is cheap.
  Not "getter for `_x`".
- **Private functions.**
  The audience shifts to a maintainer inside the module, so implementation-adjacent detail is legitimate.
  Do not accept line-by-line narration, but apply the public caller test less strictly.

## Defer to repo convention

- **Convention and format.**
  The repository convention and configured linter decide.
- **Coverage.**
  Whether private helpers, overrides, or test functions carry docstrings is the repo's call.
  Match the surrounding files.

## Signals this lens produces

- A docstring that can only restate the function name is a prompt to check whether the name hides something, not a prompt to pad the docstring.
  Report the naming doubt to the semantic-naming lens; do not fix it here.
- When evidence establishes that a behaviorally testable contract clause lacks coverage, keep the clause and record a missing-test observation in the ledger for `code-review`.
