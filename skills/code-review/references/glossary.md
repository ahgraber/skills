# Glossary

The standard and deep reviews use each of these words for one thing only, in the procedure, the templates, and `scripts/review_state.py`.

## The plan

- **Partition**: one feature of the domain that the changed code handles, stated in the domain's own terms; identified by its `partition_id` (`P3`).
- **Input form**: a kind of input a partition's code must handle correctly, including state the code reads and settings an earlier call changed; never a concrete value.
- **Pending input forms**: the input forms of a partition that still need checking in this review.
- **Origin**: where a partition came from: the domain's reference, the implementation's tables, the spec's input spaces, or a generic construct in the diff.
- **Component**: a set of changed files that one subagent reads together: files that call each other, or that the same tests cover.
  With several components, each gets its own quality lens and test adversary, and in a deep review its own list builder.
- **Partition list**: the repository's saved partitions, kept across reviews in the state file.
- **Inspection**: one inspector's check of one partition: the file content it saw, and each input form's status (`handled`, `claims`, or `not checked`).
- **Too coarse**: an inspector's report that a partition has too much to check in one pass; the keeper splits it into child partitions.

## The review

- **Depth**: `standard` or `deep`.
  A standard review dispatches the lenses, the test adversary, a consolidator, a challenger, and the synthesizer.
  A deep review adds the partition list with its inspectors and rounds, the runners, the hunters, and the forms checker.
- **Review**: one standard or deep review, identified by its `review_id` (`<UTC date>-<UTC time>-<short head>`), with its own directory under `reviews/`.
- **Packet**: the diff, the changed-file list, and the source of truth, in one file the roles read by line range.
- **Root**: the repository root; every path in an input file is relative to it.
- **Round**: one pass of inspectors, then judging, hunting, and refinement of the partition list.
- **Convergence**: from round 2 on, half or more of a round's inspector claims repeat records grouped in an earlier batch.
- **Plan frozen**: the state after a round has inspected every partition it started with and either converged or was round 2, the last round: no further round starts, and that round finishes its own work, including inspecting the pieces of its too-coarse partitions.
- **Dispatch**: one assignment of one role to one subagent, identified by its `dispatch_id` (`D4`); it is open until its output is submitted.
- **Pending**: the work waiting for each step, listed by `status --review`: `inspect`, `consolidate`, `run`, `challenge`, `hunt`, `refine`, `rule`, and `check_forms`.

## Roles

- **Finder**: a role that writes claims: the inspector, the quality, security, and spec lenses, the test adversary, the forms checker, and the hunter.
- **Judge**: a role that decides claims: the runner and the challenger.
- **List builder**: proposes partitions for one component.
- **Partition keeper** (`keeper`): the only role that changes the partition list.
- **Inspector**: checks one partition's pending input forms against the code.
- **Lens**: reads the change from one viewpoint: quality, security, or the spec; the quality lens reads one component at a time when the change has several, and so does the test adversary.
- **Test adversary**: asks what wrong implementation the tests would accept, and runs a probe for each.
- **Forms checker**: after the loop, finds the tests that exercise each input form of the touched partitions, and probes each form no test exercises.
- **Consolidator**: marks duplicates and puts every other record in a failure mode.
  It places a misgrouped record again, and restates the description of the failure mode that record left.
- **Runner**: runs each record's input as a probe.
- **Challenger**: argues the author's side on each record a run cannot settle.
- **Hunter**: for one failure mode, checks each record's expected result against its source, then finds the other places that have the same fault, and names suspected input forms.
  Its output states `expected` (the records' expected result as one rule for a set of places), `searched` (what produces every place the rule applies to, and where it is), and `sites` (each of those places, with a status of `handled`, `claims`, or `not checked`, and the reason).
  It lists in `misgrouped` each record it was given that breaks a different rule than `expected`.
- **Synthesizer**: writes the report.

## Claims and records

- **Claim**: a finder's write-up of one suspected defect: the site, the input form, the expected result and its source, the observation, and a proposed failure mode.
  It is kept as written.
- **Record**: the stored item for one claim, identified by its `record_id` (`R2-4`), with each decision made about it: its grouping, its run, its challenge, its hunt, each `misgrouped` entry, and the user's ruling.
- **Failure mode**: the way the code fails, which other sites can share: a name, and a description of the mechanism (the kind of input, the operation it reaches, the missing guard or wrong assumption) without a file, function, or variable name.
  Its name is its identity.
- **Duplicate**: a record that is the same defect as another record, its **primary**.
- **Split**: the script undoing a duplicate link when the two records' runs disagree; the record keeps its primary's failure mode.
- **Misgrouped**: a hunter's finding that a record it was given breaks a different rule than the other records of its failure mode.
  The first time, the record leaves the failure mode, and the consolidator places it again, in another one.
  The second time, it stays where it is, and the report says that no hunt covered it.
  The record's `misgrouped` holds one entry for each time: the failure mode, the hunter's reason, and the hunter's dispatch.
- **Suspected input form**: an input form a hunter suspects of triggering a failure mode; the keeper adds it to the partition list.

## Verdicts

A record's verdict comes from its decisions; the first that applies wins: a duplicate link, the hunter's check of the expected result, the user's ruling, the challenger, then the run.

- **confirmed**: a run showed the defect.
- **refuted**: a run, the challenger, or the user showed the claim is wrong.
- **test gap**: the code behaves correctly, and no test checks it.
- **not runnable**: a probe could not run or did not reach the path; it does not settle anything, so the challenger decides.
- **upheld**: the challenger or the user found the evidence sound.
- **disputed**: the challenger could refute neither side, or the verdict depends on author intent that the intent and spec do not settle; the user rules when its priority is critical or high.
- **duplicate**: the record repeats its primary.
- **unsupported**: the source the claim cites does not support its expected result.

The report groups records by verdict:

- **Candidate**: a record with no verdict yet.
- **Finding**: a record that is confirmed or upheld.
- **Dropped**: a record that is refuted, a duplicate, or unsupported.

## Names in the files

- A field named `<kind>_id` holds an identity of that kind (`record_id`, `dispatch_id`, `partition_id`, `review_id`); a role prefix says which one (`primary_id`, `keeper_dispatch_id`).
- A field named `<kind>_hash`, or `<kind>_hashes` for a map of them, holds a content fingerprint (`file_hashes`: each path's git blob id).
- A field named with a bare noun holds the thing itself (`claim`, `grouping`, `run`).
