# Claim

`review_state.py` fills the `{{claim}}` slot of each finder prompt with the \`\`\`text block below.
`submit` checks every claim against the `Claim` model, and a test checks that this list names exactly the model's fields.

```text
## Claim
Write each claim as a JSON object with exactly these fields. Use null only for a field whose line below allows it.

- site: "file:line" of the code that is wrong
- input_form: the input form this claim tests: one of the forms you were given, or "new: <form>" for one you found
- input: the distinguishing input (one on which the correct implementation and this one give different results), as one string, or null when you cannot give one
- expected: the result the correct implementation gives
- source: where the expected result comes from (a section of the domain's reference, a spec clause, documented behavior), or null
- predicted: the result you expect this implementation to give
- observation: what is wrong and why it matters, in one or two sentences
- direction: the suggested fix, in one sentence
- priority: "critical", "high", "medium", or "low"
- reachable: "yes" when a real caller or user of the changed code can produce this input (say how in observation), "no" when only a direct call with a crafted value can, "unknown" otherwise
- introduced: "this change" when the diff introduced the behavior, "pre-existing" when the code before the change already behaved this way, "unknown" otherwise
- failure_mode: {"name", "description"}: the way the code fails, which other sites can share. name: a few words. description: one sentence on the mechanism (the kind of input, the operation it reaches, and the missing guard or wrong assumption), without a file, function, or variable name, so that someone could find another instance in a different file from the description alone
- run: null, except for roles told to run their own probes

Priority:
- critical: data loss, a security breach, or a crash on a common path
- high: a wrong result that ordinary use will hit
- medium: a wrong result in an edge case, or changed behavior that no test checks
- low: style, naming, or minor maintainability
Judge priority by what a user of the software meets, not by how sure you are; reachable and introduced carry the rest.
```
