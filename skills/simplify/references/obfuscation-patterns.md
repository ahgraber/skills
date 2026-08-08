# Obfuscative Complexity

Complexity that makes code hard to _read_ rather than hard to _branch through_.

Cyclomatic complexity counts paths, and a tool can measure it.
Obfuscative complexity is structure that adds no capability and costs comprehension: a reader must hold more in their head than the behavior warrants.
A function can score 1 on every complexity metric and still be obfuscative: six files of indirection to reach one assignment.

Resolving it is usually a Tier 1 edit: collapsing an unnecessary layer or flattening nesting preserves behavior exactly, and the verification rung confirms it on the spot.
It becomes Tier 2 when the fix touches an exported contract or when preservation cannot be verified now — a wide impact radius is the usual warning sign.

## The disconfirming test

Every pattern below has a legitimate form.
Before flagging, try to find the second consumer, the published extension point, or the test seam that justifies the structure.
If you find one, the structure is doing its job, so leave it.
Flag only when the justification is absent, not when it is merely unstated.

## Patterns

### Indirection without abstraction

Layers that forward without deciding, adapting, or protecting anything.

- Wrapper functions whose body is a single call with the same arguments
- Interfaces, protocols, or ABCs with exactly one implementation
- Factories that construct one type unconditionally
- Registries, dispatch tables, or plugin maps with one entry
- Re-export modules that only re-export

_Legitimate when:_ the seam is a published extension point, a mock boundary an existing test uses, or an import-cycle break.

### Premature generalization

Flexibility built for a caller that does not exist.

- A parameter, keyword, or config flag with exactly one call site that always passes the same value
- A strategy or hook slot with one strategy
- Generic type parameters instantiated at one type everywhere
- `**kwargs` pass-through that forwards a fixed, known set

_Legitimate when:_ a spec, public API, or documented plugin contract requires the seam.

### Control-flow obscurity

Behavior that is present but hard to trace.

- Boolean parameters that switch behavior, where `render(doc, True)` at the call site tells the reader nothing
- Nested or chained ternaries
- Negated conditions where the positive reads plainly (`if not is_missing`)
- Deep nesting where an early return or guard clause flattens it
- `else` after a branch that always returns
- Loops that mutate a flag which a later branch reads

### Action at a distance

Effects that a reader cannot see from the call site.

- Functions that mutate arguments or module-level state instead of returning
- Implicit globals or singletons written from several modules
- Decorators, metaclasses, or `__init_subclass__` that change behavior invisibly
- Monkeypatching outside test setup
- Import-time side effects

### Vocabulary drift

One concept wearing several names across a change.

- The same value called `user`, `account`, and `principal` in three adjacent layers
- A wrapper that renames its argument for no reason
- Names that disagree with the codebase's existing term for the concept

Prefer the codebase's established term over the one introduced by the change.

### Data shapes that hide structure

- Dicts of dicts, or tuples indexed positionally, where a dataclass or named type fits
- Stringly-typed dispatch where an enum or literal union already exists
- Parallel lists that must stay index-aligned
- Optional fields that are always set, or never set, in practice

### Defensive noise

Handling for conditions that cannot occur.

- `try` / `except` that catches and re-raises unchanged
- `None` checks after a guarantee the type system or a prior guard already gives
- Re-validation of the same input at every layer, where one boundary already validates
- Broad `except Exception` around code with one narrow failure mode
- Assertions restating a signature's type annotations

_Legitimate when:_ the guarantee comes from an external boundary, or the check exists because the invariant was once violated in production.
Check history before removing.

### Ceremony

Structure with no behavior.

- Getters and setters that only read or assign
- Builders for objects with two fields
- `__init__` that only assigns arguments where a dataclass fits the codebase's idiom
- Constants aliasing constants
- Classes with one method and no state
