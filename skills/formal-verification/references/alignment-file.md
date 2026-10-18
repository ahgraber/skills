# The alignment file

The alignment file records what a verification effort is for and what it has established.
Any stage can be entered in a new session, so the file, not the conversation, carries the purpose, the approvals, and the results.

## Location

Ask the user where to keep verification artifacts the first time you create an alignment file.
Recommend `.verify/<effort>/`, where `<effort>` is a short kebab-case name for the effort.
Record the chosen directory in the file.

All verification artifacts stay outside source directories and outside prose-spec directories (`specs/`, `openspec/`, `.specify/`, or the repo's equivalent).
The exception is inline contracts, which live where the tool requires them.

| Artifact                                                                                                                          | Location                                                                                                        |
| --------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| Alignment file                                                                                                                    | `<dir>/alignment.md`                                                                                            |
| Saved checker output                                                                                                              | `<dir>/output/`                                                                                                 |
| Standalone model (TLA+, Alloy, P, Quint)                                                                                          | The repo's existing location for models, if it has one outside source and prose specs; otherwise `<dir>/model/` |
| Separate statement file for a code-level proof (Lean statements, SPARK `.ads` specs, Dafny abstract modules, C headers with ACSL) | Where the tool and the build require it; list the path in the alignment file                                    |
| Inline contracts (Verus, Dafny, SPARK, ACSL)                                                                                      | In the source file, where the tool requires them; list the paths in the alignment file                          |

Keep the alignment file in its own directory even when the repo uses SDD, OpenSpec, or Spec Kit.
A change directory is archived when the change closes, and maintenance needs the file after that.

## Requirements source

- If the repo has prose specs (SDD, OpenSpec, Spec Kit, or similar), the requirements are those specs.
  Cite each requirement by its ID or heading and path.
  Do not copy requirement text into the alignment file.
  Do not edit the prose specs.
- If the repo has no prose specs, write the requirements in prose in the alignment file's Requirements section, and get the user's approval of that list.
  You can mention once that SDD would hold these requirements; continue either way.
- If no requirements exist and the user does not want to state them, record user:spec as open.
  A specification derived from code or from a published protocol then describes that source.
  The report must not present it as the user's intent.

## How stages use the file

The file grows by stage.
Start from `assets/alignment-template.md`, and add a section only when the job enters the stage that owns it.
Do not show the user the sections of stages the job has not entered.

The Stages entered section lists each stage with the date it was entered.
An entry check uses that list to tell two cases apart:

- a section is missing because the job never entered that stage, which is normal;
- a section is missing because a stage was skipped on the way to the current one, which the entry check reports.

## Approvals and the freeze

Each approved statement records its files, the commit at approval, the approver, and the approval route.
The approval route is one of:

- **read** — the approver read the formal statement;
- **back-translation** — the approver approved from the blind back-translation and the can-fail checks.

Record the route as a fact.
Do not label either route as weaker or stronger.

The freeze check is:

```sh
git diff --exit-code <approved-commit> -- <statement files>
```

A non-zero exit means a statement changed after approval.
Stop and take the change to the user, with what it removes.
After the user approves the change, record the new commit.

## Retirement

When the user decides to stop maintaining a model or proof, mark it retired in the Results section with the date and the last commit at which it was current.
A retired result stays in the file and cannot be cited as current evidence.
