# Stage 4: Check or prove

This stage runs the checker or prover against approved, frozen statements.
What it establishes depends on the verified object:

- **a model**: the design has the property, within the bounds for a model checker or without bounds for a proof; the code is untouched;
- **the shipped code**: the code meets its contracts, given the tool's trusted base (solver, compiler, extraction) and the listed assumptions;
- **a translation**: the translation has the property; the gap to the code is the same as for a model.

## Entry check

- Every statement this stage uses has an approval with a recorded commit.
- The freeze check passes for those statements (see `alignment-file.md`).

## Procedure

1. Run the freeze check.
   Stop on a non-zero exit.
2. Run the checker or prover.
   Save the full output to `<dir>/output/`, named for the tool, the target, and the commit.
3. On a failure, classify it before changing anything (below).
4. On a pass, run the tool's gates from `tools.md`: list the assumptions and axioms, and scan for escape hatches in the final certificate.
5. Run the freeze check again.
   A proof that passes against a changed statement proves the wrong thing.
6. Dispatch the result audit (below).
7. Record the result in the Results section: verified object, tool and version, command, commit, covered paths, bounds, assumptions, output file, audit outcome.
   Record a find-bugs finding in the Findings section with its reproduction.

## Classifying a failure

A counterexample or a failed obligation has one of these causes:

| Cause                                                                                           | Who changes what                                                                              |
| ----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| A bug in the code or design                                                                     | Fix the code or the design. No approval needed for the code; a design change goes to the user |
| A wrong proof, hint, or loop invariant                                                          | Fix the proof                                                                                 |
| A wrong statement, property, fairness assumption, or bound                                      | Go to the user with what the change removes; after approval, re-enter stage 3                 |
| A modeling limit (the model allows behavior the system cannot have, or forbids behavior it has) | Go to the user; a model change is a statement change                                          |
| A timeout or a prover limit                                                                     | Shape the code or the query; record what could not be proved                                  |

Before blaming the prover, run the code with assertions enabled or replay the counterexample.
An SMT-backed tool usually reports "unknown" or a timeout with no counterexample, so first separate a false claim from one this solver cannot prove.
Check the requirement before deciding the statement is wrong: if the requirement supports the statement, the code or design is the suspect.

Repair loops stop improving after three to five rounds.
Feedback that does not point at the failing part makes the agent oscillate.
After five rounds with no progress, stop and report to the user.

## What cannot be proved

Each obligation that is not proved gets a written justification a reviewer can check, and the justification goes into the report.
The work is done when every obligation is proved or justified, and the assumptions are listed.

## Escape hatches and gates

Agents use escape hatches (constructs that make the checker accept an unproved claim) and switch to the next one when one is blocked.
Observed examples: `assume`, `admit`, `Admitted`, `sorry`, new axioms, redefined notation or types that make an unchanged theorem statement mean something easier, and switching verification off for a unit.
A rule in a prompt reduces this and does not stop it.
The gates that work are mechanical:

- the freeze check, which catches any change to a statement;
- the tool's assumption and axiom listing on the final certificate, compared against an allowlist the user approves;
- for Lean, Comparator, which checks the elaborated statement against the trusted statement file.

Gate the final certificate, not every file: test harnesses use escape hatches legitimately.
`tools.md` lists the gates and known escape hatches per tool.

When a symbolic procedure can decide something (for example, an IC3 engine searching for an inductive invariant), let the procedure own that decision and give the agent a narrower role.

## Result audit

Dispatch a fresh-context subagent (see "Independence" in `SKILL.md`) with this brief, filled in:

```text
You audit a verification result you did not produce.
Inputs: the alignment file <path>, the saved output files <paths>, the statement files <paths>.
For each result and finding:
- confirm the cited output file exists and shows what the alignment file claims (pass, failure, bounds, assumptions);
- confirm the freeze check passes for the statements the result depends on;
- confirm the assumption listing contains only allowlisted items;
- for each finding, run the reproduction and confirm it shows the claimed failure.
Report each mismatch with the file and line.
```

A result with an audit mismatch is not recorded as current.
In one agent study, a model faked 6 of 39 bug reproductions despite instructions forbidding it.
