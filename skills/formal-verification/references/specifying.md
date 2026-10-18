# Stage 2: Specify

This stage writes the formal statements and traces each one to a requirement.
Writing a statement from intent is the task where agents are weakest, so the trace and the layout matter as much as the formulas.

Gap: user:spec.

## Entry check

- The Purpose and Decision sections exist.
- The requirements are listed, or user:spec is recorded as open.

## What you write depends on the kind of work

| Kind of work                 | Tools                             | What you write                                                                    | The hard decision                                                              |
| ---------------------------- | --------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| Design model checking        | TLA+, Alloy, P, Quint, Spin       | A state machine, a type invariant, properties, a configuration with finite bounds | What to leave out, how coarse each atomic step is, which actions get fairness  |
| SMT-backed code verification | Dafny, Verus, SPARK, F\*, Frama-C | Contracts, loop invariants, ghost code, lemmas                                    | How strong a property to prove, over how much of the code                      |
| Interactive proof            | Lean, Rocq, Isabelle              | Theorem statements, an executable intermediate specification, refinement layers   | Which layers to introduce, and how to shape the code so the proof is tractable |
| Refinement methods           | B, Event-B                        | An abstract machine and refinement steps                                          | The order of refinement steps                                                  |

## Procedure

1. Write the properties in the user's terms first, one per requirement, as a list the user can read.
   Prefer properties stated in terms an outside observer can see.
2. Fill the Properties and trace section in both directions:
   - each property names the requirement it comes from and its origin (user, derived from code, published spec);
   - each requirement names the property that covers it, or the reason it is not covered.
3. Choose the layout for the freeze (below) before writing formal text.
4. Write the formal statements.
   Apply the practices for the kind of work.
5. Record the model's omissions: what it leaves out and why.

## Practices for design models

- Model one slice of the system.
  Leave things out by default, and record each omission.
- Keep the type invariant separate from the correctness properties.
- Start coarse.
  After a clean run, split actions into finer steps; coarse steps hide races, and a clean run on a coarse model is a reason to refine, never a reason to stop.
- State fairness per action, never on the whole next-state relation.
  A fairness assumption is a claim about the real scheduler, and the user approves it.
- Check liveness in a separate model with smaller constants.
  Agent-written liveness properties fail far more often than safety properties.
- Model the environment (users, networks, other services) apart from the system.
  Write environment limits as named assumptions.
  Never constrain the environment to make a check pass.
- Do not let one process read state it could not observe in the real system.
- Do not assume a published protocol specification describes this system.
  Implementations differ from their published specs; write or adapt the model for this code.
  A model recited from training data, or textbook invariants that ignore this system's code, is a known agent failure.
- If stage 5 will apply, write the model at the implementation's level of detail.
  A model written abstractly for design insight did not match the code in a documented trace-validation failure.
- Prefer one model of the slice.
  Joining separately written models tends to over-constrain the result; use rely-guarantee assumptions between components only when the question crosses component boundaries.

## Practices for code-level proofs

- Choose the level of rigor and the subset of code first.
  Absence of runtime errors is often the right goal for most of the code.
- Shape the code for proof: small functions, small solver queries.
- Reshaping code is a change to the user's code.
  Describe the change and get the user's agreement before making it.

## Layout for the freeze

The freeze in stage 3 is a whole-file comparison, so each statement and every definition it depends on must sit in files that hold nothing else the agent edits during proving.

| Tool                  | Layout                                                                                                                                                  |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| TLA+, Alloy, Quint, P | The spec file and the checker configuration are already separate; freeze both                                                                           |
| Lean                  | Theorem statements and the definitions they use in a statement file; proofs elsewhere. Comparator checks that the proof proves exactly those statements |
| SPARK                 | Contracts in the package spec (`.ads`); bodies in `.adb`                                                                                                |
| Frama-C               | ACSL contracts in headers                                                                                                                               |
| Dafny                 | Specification in an abstract module, refined by an implementation module                                                                                |
| Verus                 | No separation known. The freeze for these statements is the user's review of the diff, and the report says so                                           |

The Lean and TLA+ rows are documented in published practice.
Confirm the other rows against the tool's documentation and the project's build before relying on them.
When the layout is not possible, record in the alignment file that the freeze for those statements is a person's review, not a mechanical check.

## Specifications derived from code

When the input is existing code (for example, an agent instruments the code and models it from traces), the model describes the code.
It can find bugs only where the code disagrees with something else.
Relate it to the user's requirements:

1. Trace each derived property to a requirement, or mark it "derived from code, not confirmed by the user".
2. List requirements that no property covers.
   Without this list, a derived model looks complete because it describes the code.
3. When the code's behavior and a requirement disagree:
   - the requirement supports the property: the code is the suspect; record a candidate finding;
   - the requirement is silent: ask the user which is intended;
   - no requirement exists: record user:spec as open for that property.
4. Never adjust a property to match observed code behavior without the user's decision.
   An invariant revised to match the code removes the check that would have found the bug.
