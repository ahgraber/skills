---
name: commit-message
description: |-
  Use whenever a Conventional Commit message is being drafted — whether the user asks ("write commit message", "draft commit from staged changes", "generate conventional commit", "split this into commits") or you are about to propose one proactively after finishing work (e.g. completing tasks, wrapping up a feature, or summarizing staged changes). Invoke before writing the message inline. Not for creating commits, amending history, or full code review.
---

# Commit Message

Draft a Conventional Commit message from staged changes.

## Invocation Notice

- Inform the user when this skill is being invoked by name: `commit-message`.

## Critical Constraints

- Use only staged changes (`--cached` / staged SCM state) as input, unless the user invokes the **Context Override** or **Commit Train** path.
- Resolve and use the repository root for all SCM calls.
- If no staged changes exist after one retry, stop and inform the user (standard workflow only).
- Always include an `AI-assistant: <AGENT>` footer.
- Output only commit messages, one per markdown code block, with no commentary around them.
- Body content: apply **Body Discipline** (below) at draft time, not as an afterthought.

## Paths

| Situation                                                                                                                      | Path                 |
| ------------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| Staged changes exist and land as one commit                                                                                    | **Workflow**         |
| The user points at prior conversation work or a working document instead of the diff ("use what we just did", "skip the diff") | **Context Override** |
| The work is meant to land as several commits                                                                                   | **Commit Train**     |

Body Discipline governs the body on all three.

## Body Discipline

These rules govern body content.
Apply them at draft time (step 8) and re-check before output (step 10).

### Cold-reader test

Your reader meets this commit in two phases: **Scan mode** — they see the subject in `git log`, `git blame`, or a bisect and decide whether to open it.
**Read mode** — once opened, they read the diff and the durable artifacts around it: the specs, design docs, ADRs, README, changelog, and docstrings present in the repo at this commit.

The **subject** carries scan mode — name the area and effect concretely enough to distinguish from neighbors.

The **body** exists only when read mode leaves a question unanswered.
If no gap exists, ship subject-only — most commits.
Conversation weight is not reader weight: what felt load-bearing in the dialogue is rarely what the diff fails to convey.

Triggers 2 through 6 fire only where read mode leaves the answer missing.
A docstring, an error message, or a comment carried in the diff that already states the why closes the gap, and no body line survives on top of it.
Orientation is the exception: it answers a reconstruction burden spread across files, which the diff's own prose does not relieve.

A body line is warranted only when it fires one of these **6 triggers**:

1. **Orientation** — the commit introduces a user-facing capability whose shape a reader can't get from the subject and would otherwise have to reconstruct across several files.
   Name what it does and what it operates on; naming the knobs without saying what the capability does is inventory rather than orientation.
   Does not fire for internal refactors, for single-file changes, or where the subject already conveys the shape.
2. **Why this choice** — the subject names a choice but not the constraint that forced it.
3. **Tuning rationale** — the reasoning behind a magic number, threshold, or tunable a future reader will want to revisit.
   A bare list of values is inventory; the trigger fires only where the body supplies a why the diff cannot.
4. **Wrong-fix guards** — foreseeable "fixes" that would re-break the change.
5. **Cross-cutting impact** — callers, consumers, or schema implications the diff doesn't reach.
6. **External references** — issues, advisories, RFCs.

### Budget

A trigger licenses a line; it does not oblige one.
Where no trigger fires, ship subject-only, as most commits should.

Otherwise the body gets one short paragraph per capability the change introduces, plus at most one more carrying everything the other five triggers earned between them.
A short paragraph runs one to four wrapped lines, and most bodies come to one or two.

Count capabilities, not named surfaces: a command's own flags and subcommands belong to it, and surfaces that only make sense together are one capability.
Where orientation still runs long, compress it to the capability level first; if it will not compress because the capabilities are unrelated, the commit is doing several things and wants splitting (see **Commit Train**).

When the other triggers overflow their single paragraph, the surplus rationale belongs in a design doc or spec.
Keep whichever line a reader is most likely to be hurt by not knowing, and drop the rest.

### Durable-artifact routing

Where the repo keeps specs, design docs, or ADRs, those artifacts are the versioned home for contracts and rationale, and the commit body is not.
Route only to what an artifact carries now, in this change or already in the repo; a doc that has yet to be written is not a home.

- A contract already stated in an in-repo spec, design doc, or ADR → don't restate it.
  A body copy is unversioned and goes stale independently of the artifact it duplicates.
- Why-this-choice and wrong-fix rationale, where the change ships a design doc that can hold them → record it there.
  Reserve the body for a hazard with no home in those artifacts.

Announcing that this change fires an obligation the spec defines is not a restatement of it.
The spec states the rule; the commit reports that it just fired, and which value it landed on.

This does not suppress orientation.
Shape is what a reader invokes and what comes back; contract is the terms that answer holds to, including its normative guarantees, thresholds, exhaustive conditions, and edge cases.
Naming the shape orients a reader who has not opened the spec, while reproducing the contract duplicates it.
On a borderline line, ask which document a reader would cite to settle a dispute about it — if that document is the spec, let the spec carry it.

### Trigger-naming rule

For every body line you are about to write, name which of the 6 cold-reader triggers it fires.
If you can't name one, don't write the line — it's conversation weight or file inventory, not reader signal.
"It feels useful to mention" is not a trigger.

A fired trigger is necessary, not sufficient.
Where the answer already lives in a durable artifact or in the diff's own prose, the line still doesn't survive: routing and the Cold-reader test both outrank the trigger that licensed it.

### Line-level filters

- Restates the subject → drop.
- Names an internal symbol → restate as the public-surface description.
- Describes how, not what → restate as outcome.
- Inventories file contents (line counts, lists of topics covered, lists of items the file enumerates) → drop, the diff already shows this.
- Restates a contract recorded in an in-repo spec, design doc, or ADR → drop (see § Durable-artifact routing).
- Bookkeeping (file moves, archive, sync, lockfile) → drop unless the reader needs to act.
  A version or schema bump that consumers pin to fires cross-cutting impact and stays.

## Workflow

01. Select the path (see § Paths).
    If it is not the standard path, follow that path instead of the rest of this workflow.

02. Resolve repository root.
    Prefer workspace root when known; otherwise run `git rev-parse --show-toplevel`.

03. Retrieve staged changes with `git -C <repo-root> diff --cached`, or with the harness's SCM tooling where it offers one scoped to an explicit repo root.
    A large diff can exceed one tool call's output limit, so check what you received against `git -C <repo-root> diff --cached --stat` and page through the remainder before drafting; a message written from the first page reads complete.

04. Validate staged content exists.
    If empty, retry once with explicit repo root; if still empty, inform user and stop.

05. Analyze the staged diff.
    Identify changed files, behavior impact, logical scope, and likely commit type.

06. Calibrate to the repo.
    Read recent bodies for the changed paths (`git -C <repo-root> log -5 --format='%B' -- <changed paths>`) and match the house convention.
    Calibration governs how much to write and in what shape; it can lower the Budget but never raise it.

07. Incorporate user arguments/context when provided.
    Preserve explicit issue refs and constraints from user input.

08. Apply the **Cold-reader test**, **Budget**, and **Trigger-naming rule** (see § Body Discipline) to decide whether the body is warranted and which lines to write.

09. Read `references/conventional-commit-rules.md`.
    Then draft the message covering only the lines named in step 8, applying those rules.

10. Self-check before returning, in order:

    - **Budget** — if no trigger fires, drop the body; otherwise hold to one paragraph per capability plus one for everything else
    - **Trigger-naming rule** — name the trigger each surviving line fires; drop any line that fires none
    - **Durable-artifact routing** — drop any line the spec is the authority for
    - **Line-level filters** (see § Body Discipline)

    Revise or drop any failing lines before output.

11. Return only the final message in a fenced code block, ready for `git commit -F -`.

## Context Override

Use this path when the user explicitly directs you to draft from prior conversation work or a working document rather than from the staged diff.
**Body Discipline applies here too** — conversation-derived drafts are the highest-risk source for conversation weight.

1. Identify the source the user pointed to: prior turns in this conversation, a referenced todo list, a plan, a handoff note, or another working document.

2. Extract the scope, intent, and behavior changes from that source.
   Do not run `git diff` or any other SCM inspection.

3. If the source is ambiguous or insufficient (no clear scope, type, or "what changed"), ask the user one targeted clarifying question or fall back to the standard workflow — do not invent details.

4. Apply the **Cold-reader test**, **Budget**, and **Trigger-naming rule** (see § Body Discipline) to decide whether the body is warranted and which lines to write.

5. Read `references/conventional-commit-rules.md`.
   Then draft the message, preserving any explicit issue refs and constraints the user provided.

6. Self-check before returning, using the same ordered list as workflow step 10.

7. Return only the final message in a fenced code block, ready for `git commit -F -`.

## Commit Train

Use this path when the work spans several logical commits and is not yet staged.
The staged-changes constraint does not apply; each message is drafted from its own group's diff.

1. Group the changed paths by concern, one group per commit you intend to propose.

2. Calibrate once (workflow step 6) against the areas the train touches, and apply that calibration to every message.

3. Draft each message from its own group's diff (`git -C <repo-root> diff -- <paths>`), applying Body Discipline per message.
   Budget applies per commit.

4. Present the whole train before anything is staged: the grouping, then the messages in commit order.
   Staging and committing remain the user's call.

5. Return each message in its own fenced code block, in commit order.

## References

- `references/conventional-commit-rules.md` - subject/body/footer rules and examples.
