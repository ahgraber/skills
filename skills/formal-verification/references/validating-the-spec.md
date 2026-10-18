# Stage 3: Validate the spec

This stage shows that each statement says what the requirement means and that the checks built on it can fail.
No formal tool answers the first question; only evidence from outside the statement's author does.
The procedure is the same in both modes.

Gap: user:spec.

## Entry check

- The Properties and trace section exists.
- The statement files exist in the layout chosen in stage 2.

## Procedure

Run all four steps.
Each step catches a failure the others miss.
Save the output of every run in `<dir>/output/` and cite it in the Validation section.

### 1. Check the trace

Confirm both directions of the trace are complete: every property has a requirement or a recorded origin, and every requirement has a property or a recorded reason.
The trace catches extra and missing properties.
It does not catch a property that misstates its requirement.

### 2. Blind back-translation

Dispatch a fresh-context subagent (see "Independence" in `SKILL.md`) with this brief, filled in:

```text
Read only these files: <statement files and checker configuration>.
Do not read any other file in the repository, and do not ask what the statements are for.
For each named property, assumption, fairness condition, and bound, write in plain language:
- what behaviors or inputs it allows;
- what behaviors or inputs it forbids;
- any case where it holds trivially (an implication whose condition never holds, a state never reached).
Quote the formal text you are describing next to each description.
```

The subagent must not see the requirements, the alignment file, or this conversation.
An agent that knows the requirement describes what the requirement meant, not what the formula says.

Put the back-translation next to the requirements, one row per property, and give the comparison to the user.
Mark each row where the two differ.
Each difference goes to the user; do not resolve it yourself.

### 3. Can-fail checks

Use the commands for the chosen tool in `tools.md`.

- **Discrimination.**
  Known-bad cases must be rejected and known-good cases accepted.
  Sources: the SDD scenarios when the repo has them, past bugs and their reproductions, and cases the user names.
  For a model, a known-bad case is a behavior that must violate a property.
  For a contract, it is a wrong implementation or output that must fail, and a correct one that must pass.
- **Vacuity and reachability.**
  Confirm that the states each property depends on are reached.
  The portable method: add the negation of a reachability claim as an invariant, and expect a counterexample.
  For an implication, confirm its condition can hold.
  Confirm the model admits the scenarios the domain requires, and that the bounds are large enough for a full cycle of the protocol plus margin.
- **Clause mutation.**
  Weaken one conjunct or clause at a time and rerun.
  A mutation that no check notices marks a clause nothing tests.
  Report it to the user.
  Mutation tools exist only as research prototypes; do this by hand for small specs, and record which clauses you mutated.
- **Liveness and fairness.**
  Write one liveness property that must fail under the stated fairness, and confirm it fails.

A check you have not seen fail does not count as a check.

### 4. Approval

Give the user, for each statement:

- the property in plain terms and its requirement;
- the back-translation comparison;
- the can-fail results, with output files.

The user approves or asks for changes.
Record the statement files, the commit at approval, the approver, and the route (read the formal statement, or approved from the back-translation and can-fail checks).
From this point the freeze applies (see `alignment-file.md`).

## Repeat after every statement change

Any approved change to a statement re-enters this stage for the changed statements.
Agents weaken statements after a counterexample: they add preconditions until a proof goes through, write a trivially true postcondition, or relax a property.
This stage, run again, is where that shows.
