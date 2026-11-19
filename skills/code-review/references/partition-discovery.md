# Partition Discovery

A **partition** is one feature of the domain that the changed code handles, stated in the domain's own terms: "here-documents feeding a pipeline", "options that change what `cd` resolves", "URLs with an IPv6 literal host".
A partition never names a file, a line, a defect, or an example input.
Each partition carries **input forms**: the kinds of input the domain allows for that feature, including state the code reads and settings an earlier call changed.
An input form names a kind of input ("an option given more than once"), never a concrete value; a concrete value ("`-o a -o b`") is an example input, and inspectors never get those.

A deep review searches for defects over the **partition list**, built before anyone looks for defects, so the search covers the domain instead of the neighborhood of the last defect found.
A standard review does not use the partition list, so this file applies only to a deep review.
The list belongs to the repository, not to a branch: each review inspects only what earlier reviews did not, and the next review starts where this one stopped.

This file covers the list: how it is built, inspected, refined, and saved.
`deep-review.md` covers the review procedure that uses it, including how claims are judged and how hunters search for more instances of a confirmed failure mode.
`glossary.md` defines the words both use.

## 1. Build the Partition List

Two roles build the list, both on a strong model:

- A **list builder** proposes partitions for one component of the change.
  Dispatch one per component when the change has parts that do not depend on each other (a component is a set of changed files that call each other, or that the same tests cover); dispatch one for the whole change otherwise.
  Template: `assets/prompt-list-builder.md`.
- The **partition keeper** merges the builders' proposals with the saved list (§ 6), and merges partitions that name the same feature.
  Template: `assets/prompt-keeper.md`.

A list builder takes partitions from these origins:

1. **The domain's reference.**
   Name the domain the changed code models: a language, a protocol, a file format, a program's command line.
   List the reference's own sections or features (a language manual's grammar sections, a protocol's message types, a format's field kinds).
   For each feature, add a partition when the changed code reads, produces, or decides on input of that kind.
2. **The implementation's own tables.**
   For each allowlist, switch table, option parser, or registry the change adds or reads, add a partition per entry class.
   Example: for each allowlisted program, "arguments that make it read or run another file".
3. **The spec's input spaces.**
   For each universal requirement in the source of truth, add a partition per input-space partition (`sdd-spec-formats.md` § 1.6 in the `sdd` skill, when the project uses it).
   Universal requirements that an `sdd-verify` run flagged belong here, as origins for the list builders; never pass them to inspectors.
4. **Generic constructs in the diff.**
   Error and exception paths, concurrency and shared state, resource lifetimes, boundary values, and data-structure invariants: add one partition for each construct the diff uses.

Each partition records its origin, because § 3 admits a new partition only when an origin names it.

**Paths.**
Each partition lists its paths: the files that handle the feature, and the files its behavior reads, such as templates, configuration, schemas, and generated tables.
An inspection counts only while those files keep the content it saw (§ 6), so a file the behavior reads but the list leaves out can change without sending the partition back.
When a saved partition already names a feature the builder finds, the builder proposes it again with the component's paths that handle it, so a new file that implements an existing feature joins its partition.

**Input forms.**
For each partition, the builder lists the forms of input the domain allows for that feature, taken from the reference and the spec, not from the code.
They include the forms a reader of the code does not see: an argument left out so that a default applies; an argument present but empty, null, or given more than once; data the code reads that the caller did not pass in; and settings that an earlier command or call changed.
Inspectors check the forms against the code, the forms checker checks them against the tests, and later reviews reuse them.

Do not take partitions from the last review's findings.

## 2. Inspect

Dispatch one **inspector** per partition in `pending.inspect`, on a small, fast model, in batches of at most 8.
Template: `assets/prompt-inspector.md`.

The script fills the template's slots; dispatch the prompt unchanged.
Do not add prior findings, prior verdicts, example inputs (concrete values), edges to probe, or notes.
Prior content steers an inspector toward known defects and lowers what it finds elsewhere.
A small scope per inspector raises its hit rate, so list only the files that handle the partition.
`review_state.py dispatch inspector --partition <partition_id>` writes the inspector's input: the packet's line ranges for its files' hunks and for the source of truth, not the whole packet, and only the partition's `pending_input_forms`.
Those are every form for a partition never inspected or whose files changed, and only the unchecked forms for a partition reopened by new forms.
Forms an earlier inspection already checked lead an inspector back to the findings already filed.

The inspector reports a status for each form: `handled`, `claims`, or `not checked`.
Only the forms it checked count as inspected; a form it did not check stays unchecked, so the next round or review checks it, and the pieces of a split inherit only what was checked.
Each claim it returns names the input form it tests, the source of its expected result, and a proposed failure mode; `deep-review.md` sends every claim to the judges.

## 3. Refine

The partition keeper refines the list after each round's hunters.
Its suspected input forms are the forms the hunters named, and the input form of each record confirmed in or moved into a failure mode after that mode's hunter was dispatched.
It takes each one, with the failure mode it may trigger:

- **It falls under one or more partitions.**
  Add it to each of them as an input form, in domain terms, without a file, a line, or a defect.
  A partition with a form no inspection checked needs inspecting (§ 6).
- **It does not fall under any partition.**
  Add a partition only when one of the origins in § 1 names the feature it belongs to, and record that origin.
  Otherwise, add it as an input form on the closest partition.
- **An inspector reported its partition too coarse, or a partition holds more input forms than one inspector can check.**
  Split it along the sections of its origin, and divide its input forms among the pieces, which the parent lists in `child_ids`.
  The pieces inherit the parent's inspections, so a piece is inspected only for forms its parent never checked.

The list stays bounded: a new partition needs an origin that names it, and the origins are finite.

## 4. Rounds

A round is one dispatch of inspectors, then judging, hunting, and refinement.
Inspect every new or split partition, and every partition with an unchecked input form, in the next round.
Stop when a round does not add a partition, a split, or an input form.

**Convergence.**
From round 2 on, when a round has inspected every partition it started with, and half or more of its inspector claims are duplicates of records grouped in an earlier batch, the search has converged, and the plan freezes: no further round starts.
The keeper's `submit` at the end of the round records the freeze; until then, a runner that splits a repeat back out can undo it.
`review_state.py status --review <review_id>` reports the count as `convergence`; duplicates within one batch do not count, and a duplicate whose run disagrees with its primary's is split back out and does not count either.
The count is only as good as the consolidator's test for the same defect: the same operation and the same kind of input, judged by meaning, not by wording or cited line.
The converged round still finishes its own work, so the review ends with nothing it took on left undone: its records are judged and hunted, the keeper splits the partitions it reported too coarse, and inspectors check the pieces.
The hunters' suspected input forms still reach the keeper, which saves them as additions to the plan; later reviews inspect them, and the forms checker covers those on the partitions this change touches.

Count rounds across the whole review, including rounds that a defect found after the loop reopens.
A deep review inspects in at most two rounds: when round 2 is inspected, the plan freezes, and later reviews inspect what this one leaves.

## 5. Coverage

A review does the full work, so that later reviews build on it instead of repeating it.

- **When no partition has been inspected yet** (the first review in the repository, or of a component the list does not cover), inspect every partition.
  State the number of partitions and the expected number of dispatches before starting.
  The scope rule is in `deep-review.md`, "Before Step A".
- **When the list exists**, inspect the partitions that need it (§ 6), the partitions the keeper adds, and the new and split partitions from § 3.
- **A quick review** does not use partitions; see `quick-review.md`.

## 6. Review State

The partition list belongs to the repository, not to a branch.
A partition describes a feature of the domain, so every branch's review reads and extends the same list, and every linked worktree shares it.
`scripts/review_state.py` keeps two files, and is the only writer of both; never edit them by hand:

- The **state file** (`review-state.json` in the review directory) holds the partition list and its inspections for the whole repository, and the finished reviews.
- The **review file** (`reviews/<review_id>/review.json`) holds one review's dispatches, records, and failure modes.
  Beside it are the packet copy (`packet.md`, `packet.json`) and the roles' input files (`in/`), output files (`out/`), and filled prompts (`prompts/`).

| When                                      | Command                                                                                                                                                   |
| ----------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Step 0                                    | `status --scope <scope>`: the review directory, `pending.inspect` with reasons, and this branch's last review                                             |
| After the packet is built                 | `start-review --scope <scope> --packet-json <file> --passed-checks <command>... --intent <text> --how-to-run <text>`: the `review_id`                     |
| To correct a value that fills the prompts | `update-review --review <review_id> --how-to-run <text>`, or another value's flag                                                                         |
| Before each subagent is dispatched        | `dispatch --review <review_id>` for the next step's dispatches, or `dispatch <role> ...` for one: the input file, the filled prompt, and `submit_command` |
| When a subagent has written its output    | `submit <dispatch_id> --review <review_id>`, run by the subagent itself; the synthesizer's records the finished review                                    |
| To decide what to dispatch next           | `status --review <review_id>`                                                                                                                             |
| When the user rules on a disputed record  | `rule <record_id> --review <review_id> --verdict upheld\|refuted --reason <reason>`                                                                       |
| Between rounds                            | `start-round --review <review_id>`                                                                                                                        |
| To see a role's output format             | `schema <role>`                                                                                                                                           |

An inspector's `dispatch` records the content hash (git blob id) of each of the partition's files as they are on disk, because inspectors read from disk and the files can change while one runs; it keeps them on the dispatch, in the review file.
The inspector's `submit` writes the finished inspection, with the status the inspector reports for each input form, to the state file, so the state file holds only finished inspections.
Two reviews that inspect the same partition at the same time therefore each record the content they saw, and an abandoned review does not leave anything in the state file.
A partition's files are the `paths` the list gives it.
New partitions arrive from the keeper as `new-<n>`; the keeper's `submit` assigns their `partition_id`s, and maps a new partition whose feature matches an existing one onto it.

A partition needs inspecting when it was never inspected, when one of its files differs from the content its inspections saw, or when it has an input form no inspection checked.
`status` compares the recorded file hashes with the content its scope reviews: the index for `staged`, `HEAD` for `branch`, the working tree for `worktree`.
A branch review checks the commit it started on, so a later commit on the branch does not change what the review checks or send an inspected partition back.
Because the comparison is by file content, an inspection still counts after the inspected change is committed, on another branch, and after a rebase.
An inspection counts only for the content it saw: a form checked on an earlier version of a file is checked again once the file changes, and the pieces of a split inherit only the checks of the current content.
Roles read and run the files on disk, so `start-review` refuses a staged or branch review whose files on disk differ from the content it reviews.
During the review, `dispatch` refuses each role that reads or runs the files while a changed file on disk differs from that content; an inspector's `dispatch` also checks its partition's files.
The keeper, the consolidator, and the synthesizer read only the review's records, so their `dispatch` does not check.
When a later commit changes a reviewed file, the refusal names the commit to check out again; `review-dispatch.md` says how to go on in a separate checkout of that commit.

Writers hold an operating-system lock on each file, re-read it, merge, and replace it atomically, so parallel calls do not lose an update, and a crashed writer does not leave a lock held.
The keeper's `submit` keeps every partition, takes the union of input forms and paths, and records splits; a split partition is no longer inspected.

The state file does not hold findings.
It feeds the partition keeper and the inspectors, and inspectors must not see prior findings.
The review file holds the findings, and only the roles that judge or report them read it.
