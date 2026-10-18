# Stage 5: Connect to code

This stage applies when the verified object is a model or a translation.
It answers one question: is the thing that was checked the thing that runs?
Most connections sample behavior, so their evidence is test evidence about the code, not proof.

Gap: spec:code.

## Entry check

A result about a model or a translation exists in the Results section.

## Choose the connection

| Connection                             | Kind                               | What it needs                                                              | What it gives                                            |
| -------------------------------------- | ---------------------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------- |
| Refinement proof                       | Proof                              | Code and model in a prover, and the effort of a large verification project | The code implements the model                            |
| Code generation from the proved model  | Proof, if the generator is trusted | A generator for the target language                                        | Generated code that inherits the model's properties      |
| Verify the shipped code directly       | Proof                              | A code-level tool for the language; often a rewrite                        | Skips the model; re-enter stage 2 with a code-level tool |
| Trace validation                       | Sampling                           | Logging at the points where operations take effect                         | Each logged run is checked against the model             |
| Test generation from the model         | Sampling                           | Control over the system's nondeterminism (scheduling, message delivery)    | The model's behaviors are run against the code           |
| Differential testing of model and code | Sampling                           | An executable model and an input generator                                 | Model and code agree on the generated inputs             |

Choose by what the code allows: logging at commit points favors trace validation; control over nondeterminism favors test generation.
Trace validation and test generation each miss failures the other catches.
Use both, or record which one ran and what it cannot see in the Connection section.

Tell the user the expected cost before starting.
Published first-time costs range from two person-weeks to two engineer-months for trace validation, and one well-staffed attempt was abandoned after ten weeks because consistent state could not be captured from multithreaded code.
An agent-run trace-validation loop has a published median of about $57 and 3.7 hours per system, measured by the tool's own authors.

## Agent-run trace validation

The loop that has published results:

1. Plan where to log: the points where each operation takes effect.
2. Instrument the code.
3. Generate the harness that replays logged traces against the model.
4. Replay with the model checker.
5. On a replay failure, classify it: a code bug, a model that does not describe the code, or a property that is wrong.

Keep the model's system description (state and actions) in files separate from the properties and fairness assumptions.
Repairs to the system description, so that it matches the code, are the purpose of this loop and do not need approval.
Each repair must be model-checked against the frozen properties.
Report every repair to the user, and flag any repair after which a previously failing property passes; that repair can hide a bug.
A change to a property, a fairness assumption, or a bound follows constraint 2 in `SKILL.md`.

A model built this way describes the code.
Apply "Specifications derived from code" in `specifying.md` before any result from it reaches the report.

## Record the covered paths

List the code paths each connection covers, and get the user's approval of the list.
The staleness check in stage 7 compares these paths against later commits.
A path missing from the list is a change the staleness check will not see.
