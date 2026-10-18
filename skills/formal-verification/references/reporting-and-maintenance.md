# Stages 6 and 7: Report and maintain

## Stage 6: Report

The report states what the evidence establishes and how it was obtained.
The user judges whether that is enough for their decision.

### Entry check

At least one result with saved output exists.

### Save and cite

- Every checker run writes its full output to `<dir>/output/`.
  Do not retype a result.
- Every pass, failure, bound, and assumption in the report cites its output file and the line it comes from.
  A claim without a citation does not go in the report.
- No script parses checker output into the report.
  Output formats differ by tool and version, and a misread format turns a failure into a pass without any sign.

### Contents, per result

- The purpose: question, decision, mode.
- The status of each gap (user:agent, user:spec, spec:code, user:code): closed or open, with the evidence for each.
- The approval route of each statement.
- The verified object, and what the result does not establish about the code.
  For a model: "a property of the model; says nothing about the shipped code without the connection in stage 5."
  For a proof about the shipped code: the trusted base (solver, compiler, extraction) and the assumption listing.
- Bounds (constants, depth, unrolling) and assumptions (axioms, fairness, environment).
- Obligations justified by review instead of proof, with the justifications.
- Elective checks that ran and that did not run.
- Staleness.

### Mode

- **Find bugs**: list findings, each with its reproduction and output file.
  Make no statement that anything is correct.
- **Establish assurance**: state each property established, on which verified object, within which bounds, with which assumptions.

Use the words the evidence supports.
A bounded model check is a bounded result, never a proof.
A pass on a model is a result about the model.

### Audit

The result audit from stage 4 also reads the report against the saved output files.
A citation that does not match its file fails the audit.

## Stage 7: Maintain

Results decay: code changes, proofs break when unrelated code changes the solver's queries, toolchains change, and models drift from the code while still being cited.

### Entry check

A prior result exists.

### Staleness check

Run at every entry (Step 0 in `SKILL.md`), for each current result:

```sh
git diff --stat <result commit>..HEAD -- <covered paths> <requirement source>
```

Any change marks the result stale.
Record the status in the Results section and show it in the report.

### Stale results

For each stale result, the user chooses:

- **re-run**: re-enter at the stage the change affects (stage 2 for a requirement change, stage 4 for a code change under a code-level proof, stage 5 for a code change under a model);
- **leave stale**: the result stays in the file, marked stale, and the report shows it as stale.

Never mark a stale result current by reading the diff and judging it harmless.

### Retirement

The user can retire a model or proof.
Mark it retired with the date and the last commit at which it was current.
It stays in the file and cannot be cited as current evidence.

### Continuous checks

Nothing runs automatically by default.
Offer the user a CI job for the staleness check, the freeze check, and the checker run; adding it is the user's choice.
For SMT-backed proofs, offer proof-stability measurement and pinned verifier versions as elective checks.
