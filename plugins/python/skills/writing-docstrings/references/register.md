# Register

## Two registers

Diátaxis (<https://diataxis.fr/reference/>) separates reference from explanation.
A generated site has no other home for explanation, so the docstring level decides the register.

- Functions, methods, and most classes are reference.
  A reader consults them and does not read them through.
  Describe and only describe: state facts, list items, and give warnings ("must", "never").
  Do not instruct, argue, or tell a story.
- Module pages and landing pages are short explanation.
  They say how the parts fit together and which concept each part owns.
  They still use plain, short sentences.

## Plain language

Write as a professional technical writer, toward ASD-STE100.

- One fact per sentence, in active voice.
- Use the same word for the same thing every time.
- Name the actor and the action.
  Write what the code does, not a metaphor for it.
  - Write "Each call to a verb uses one operation from the budget", not "Each verb call is charged to `counter`".
  - Write "Each call names a principal, and the VFS checks that principal's grants", not "Each call acts as a principal".
- Prefer the specific: the error type, the limit, the default value.
- Do not announce structure ("This function does the following:") or restate the signature.

## The caller test

A docstring states what a reader must know to use the object correctly without opening the body.
Test each sentence: would it become false after a rewrite of the body that keeps the behavior?
If yes, it narrates the body; cut it or salvage the fact inside it.

| Keep                                                  | Cut or move                                                     |
| ----------------------------------------------------- | --------------------------------------------------------------- |
| The effect, in the caller's terms                     | Body narration                                                  |
| Contract the types do not show: units, ranges, order  | The type or name restated                                       |
| Return meaning: empty against `None` against an error | Rationale for the implementation (to a body comment, or delete) |
| Errors and the conditions that raise them             | History: "previously", "no longer", "renamed from"              |
| Side effects and surprising cost                      | Pointers to specs, tickets, or conversations                    |
| Usage constraints and choice between similar calls    | Internal names a reader cannot use                              |

Salvage before you cut.
"Loops over the items in insertion order" holds a guarantee: write "Returns items in insertion order".

## Rationale

Move a sentence that explains why the code is built a certain way to a comment at the line it defends, when it stops a foreseeable wrong fix.
Delete it otherwise.
Keep a "why" in a module or landing page only when it helps a reader predict behavior, such as a scaling limit.

## Length

Length is a first filter, not a verdict.
A long docstring that is all contract needs structure, not cuts.
A short docstring can fail by packing several conditions into one sentence.
