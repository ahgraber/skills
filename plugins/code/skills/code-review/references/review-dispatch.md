# Review Dispatch

This file holds what the standard review and the deep review share: how a role is dispatched, what to gather first, the roles both reviews use, and the report.
`standard-review.md` and `deep-review.md` give each review's steps and point here for the details.
The words these files use (finder, claim, record, failure mode, and the rest) are defined once in `glossary.md`.

Subagents do the review work.
The main agent orchestrates: it registers dispatches with `scripts/review_state.py`, which writes each role's filled prompt, dispatches them, and talks to the user.
It does not judge claims, group records, refine the partition list, or read the roles' output files.
Each role reads its input file and writes its output file; `review_state.py submit` validates and records the output, and `review_state.py status --review <review_id>` tells the orchestrator what to dispatch next.

These rules (model resolution, the role set, the order of steps, and the challenger) are purpose-built for code review and take precedence over any general subagent skill (e.g. `subagent-patterns`) when reviewing code.

> **Harness note.** These files use `Agent` as the running example name for the subagent dispatch tool, and `model` as the example name for a per-dispatch model parameter.
> The templates use "Think hard." as the example phrase that engages extended thinking; where the dispatch tool has a reasoning parameter instead, set it high for the strong-model roles.
> Substitute your harness's equivalents as needed; the workflow is the same.
>
> - **Fresh context.** Every role must start without this conversation's history. If the dispatch tool copies the parent's conversation by default (for example, a `fork_turns` parameter that defaults to all turns), turn that off on every dispatch.
> - **Reading files.** The templates say "your file-read tool"; a harness without one reads files with shell commands, in bounded ranges, checking for truncated output.
> - **Concurrency.** Dispatch at most 8 roles at a time, or the harness's limit if it is lower.
> - **Recording output.** Each role runs `review_state.py submit` itself and replies only `recorded <dispatch_id>` (`submit` prints that reply and the reason for it as the last thing the role reads), so its findings stay in its output file and out of the orchestrator's context. A role that cannot run shell commands replies `not recorded: <output path>`; run its `submit_command` yourself, and if it fails, dispatch the role again with the same input and the error.

## Roles

Each role has one prompt template in `assets/`, named `prompt-<role>.md` after the key `dispatch` takes.
Every subagent prompt states that the subagent must not edit any repository file and writes only its output file; the runner, the test adversary, and the forms checker also write probes under `$TMPDIR`.
The finders are the roles that write claims: the inspector, the three lenses, the test adversary, the forms checker, and the hunter.
The judges are the roles that decide claims: the runner and the challenger.
`dispatch` refuses a role that the review's depth does not use.

| Role (`dispatch` key) | Depth | Model  | Does                                                                                                                                                 |
| --------------------- | ----- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `quality-lens`        | both  | strong | Reads the diff line by line for defects, one per component; architecture                                                                             |
| `spec-lens`           | both  | strong | Checks the change against the source of truth; dispatched only when there is one                                                                     |
| `security-lens`       | both  | strong | OWASP Top 10:2025 review of the whole change; always dispatched                                                                                      |
| `test-adversary`      | both  | strong | Finds untested behavior, tests a wrong implementation would pass, and tests that disagree with the spec; runs distinguishing inputs                  |
| `consolidator`        | both  | strong | Marks records that are the same defect, and groups the rest into failure modes                                                                       |
| `challenger`          | both  | strong | Argues the author's side on each record a run did not settle                                                                                         |
| `synthesizer`         | both  | strong | Writes the report from the placed records, and re-checks the previous report                                                                         |
| `list-builder`        | deep  | strong | Proposes partitions, input forms, and paths for one component (`partition-discovery.md` § 1)                                                         |
| `keeper`              | deep  | strong | The partition keeper: merges proposals with the saved list; refines the list after each round                                                        |
| `inspector`           | deep  | small  | Checks one partition's input forms against the code; returns claims with distinguishing inputs                                                       |
| `runner`              | deep  | small  | Writes and runs a probe for each record with an input                                                                                                |
| `hunter`              | deep  | strong | For one failure mode: checks each expected result, names the set of places that can share the fault, decides each place, names suspected input forms |
| `forms-checker`       | deep  | strong | Checks the final input forms against the tests, and probes each form that a test does not exercise                                                   |

## The Dispatch Cycle

Every role goes through the same three steps:

1. Register the dispatch.
   `review_state.py dispatch --review <review_id>`, with no role, registers every dispatch the next step names, up to `--limit` open at one time (default 8; use the harness's limit when it is lower).
   `review_state.py dispatch <role> --review <review_id>` registers one, with the role's options.
   Both write the role's input file (its assignment, its packet ranges, its output path, and its `submit_command`) and its prompt, filled from the role's template and the review's values, at `prompt_path`.
2. Dispatch the subagent with the one-line prompt `Read the file <prompt_path> in full and follow it exactly. It is your complete assignment.`, with the path filled in.
   Do not read the prompt file yourself: prompts for one role differ only in the input file they name, and reading them fills your context.
   If the harness's subagents cannot read files, send the content of `prompt_path` as the prompt, unchanged.
   It reads its input file, writes its output file, and runs `submit_command`; `submit` checks the output against the role's schema and its assignment, and the subagent fixes what `submit` rejects.
3. When the subagent returns, check its reply only for `not recorded:` (Harness note); do not read its output file.

`dispatch` prints `dispatches` (the ones this call registered), `open_dispatches` (every dispatch not yet recorded), and `next`.
Each entry has the `dispatch_id`, the `role`, the `model` class (`small` or `strong`), a `description`, and the `prompt_path`.
Dispatch every entry in `dispatches`, and run `dispatch` with no role again each time a subagent returns, so that a role the limit held back (listed in `deferred`) starts as soon as there is room; repeat until both lists are empty, then do what `next` says.
While dispatches are open, `dispatch` with no role adds only to the step they belong to, so a step's records reach the next step together.
It does not name the components of the change, because grouping the changed files is your decision ("Components" below), and it does not answer a question for the user, such as the ruling on a disputed record; `next` names those steps.
A role's option given with no role, such as `--component`, is an error.
Any file you write to prepare a dispatch, such as a helper script, goes under `$TMPDIR`, never in the review directory.

`submit` refuses output that leaves part of the assignment undone: a record without a result, a packet range not read to its end, a record placed twice or not at all, a verdict from a probe that did not reach the path.
So a dispatch is done only when every unit of its assignment is accounted for.
A dispatch that never records stays in `status`'s `open_dispatches`; dispatch it again with the same input file.
Every command that changes state is safe to repeat: `dispatch` with the same arguments returns the open dispatch (`already_dispatched: true`) instead of a second one, and `submit`, `start-review`, and `rule` return their first result.
A repeat that gives other values is refused, not dropped: `start-review` names the flags whose values differ from the started review's and the `update-review` command that changes them.
A repeated `start-review` compares only the flags it gives.
Once the synthesizer is dispatched the review cannot be changed: `update-review`, `rule`, and `dispatch <role>` refuse while it writes the report and after the review is finished, and `submit` still records an open dispatch.

`review_state.py status --review <review_id>` shows the whole state.
Its `next` field names the one next step; the other fields say why: `depth`, `open_dispatches`, `candidates` (records that do not have a verdict yet), and `pending`, which lists the work waiting for each step.
A command with `--review` uses the review's own repository; run it inside the reviewed repository, or pass `--repo <a directory inside it>`.

**Continuing in a new context.**
The review's state is on disk, so a long review does not need one long conversation.
A new session, or this one after its context is compacted, finds the review with `status --scope <scope>`, whose `unfinished_reviews` lists each review in the review directory that does not have a report yet; when more than one is listed, ask the user which to go on with.
`status --review <review_id>` then gives its `models`, the user's model choices; when it is empty, ask for them again (Prerequisites, step 5).
Continue from `dispatch` with no role: dispatch again each entry in `open_dispatches` whose subagent is no longer running, with the same `prompt_path`, and go on.
Do not keep a ledger of dispatches, records, or verdicts in the conversation; the script holds them.
In a deep review, prefer `dispatch` to `status`: `status` prints every pending item, which can be many partitions, and each line stays in your context for the rest of the session.

**When the reviewed files change during the review.**
`dispatch` refuses each role that reads or runs the files while a reviewed file on disk differs from the content the review checks, or while a reviewed file differs from the content the packet was built from; it also refuses to send an open dispatch again then.
When a staged file was staged again after the packet was built, rebuild the packet and start a new review from it.
When the changes are another person's or another session's work, do not set them aside, and do not tell a role to ignore them.
For a branch review, check out the review's commit in a separate directory: `git worktree add --detach <dir> <commit>`, or `git clone` and a checkout of the commit when you cannot write to the repository.
Build the environment there with the project's own setup command, and run `update-review --how-to-run` when the run instructions name the first directory.
Pass `--repo <dir>` to each later command; with a clone, also pass `--review-dir <the review directory>`, because a clone does not share the repository's review directory.
`dispatch` points each open dispatch at the checkout it runs in, so an open dispatch sent again reads that checkout.
The review keeps its dispatches, records, and inspections.
A staged review does not have a commit to check out: stop and ask the user.

## Prerequisites Before Dispatch

Subagents do not see this conversation.
Gather what they need first, or dispatch is wasted.

1. **Clarify intent with the user.**
   Ask, if not already clear:

   - What is this change trying to accomplish?
     Any non-obvious constraints?
   - Is there a spec, ticket, PRD, or design doc the implementation should match?
     If yes, where?
   - Any areas the user already knows are rough and wants (or does not want) scrutinized?

2. **Find how the project runs its tests and code**: the test command, the interpreter or build tool, and any setup it needs (from the README, the build files, or CI configuration); the checks gate (`SKILL.md`, Step 0) already found them.
   The roles that run probes get it in their `## How to run` slot.

3. **Decide on the architecture section** of the quality lens (below).

4. **Start the review** with `review_state.py start-review --depth <standard|deep> --scope <scope> --packet-json <the packet script's JSON> --passed-checks <command>... --intent "<what the change is for>" --how-to-run "<the test command and setup>"` (`SKILL.md`, Step 0), naming the checks that passed before the review.
   The script fills every role's prompt from `--intent`, `--how-to-run`, and these options: `--architecture yes` when the architecture section applies, `--feature-type` for the security lens, `--spec` when the spec is not in the packet (the roles that check a result against the spec are told where it is), `--flagged-claims` for the universal requirements an `sdd-verify` run flagged, whose input space their tests cover only in part (the test adversary reads them, and in a deep review the list builders too), `--domain-checks-file` for the security lens's domain checklist, and `--one-context yes` when you run the roles yourself.
   When the user did not state an intent, say so in `--intent`.
   To correct a value later, such as a run command that turned out to need another option, run `review_state.py update-review --review <review_id>` with the flags to change; prompts written after it use the new value, and the report lists each update.
   It prints the `review_id` that every later command takes with `--review`.
   It refuses a staged or branch review when a changed file on disk differs from the content the scope reviews, because the roles read and run the files on disk: the user sets the changes aside (`git stash --keep-index` for staged, a stash or a commit for branch) or reviews them as they stand with `--worktree`.
   It adds this branch's previous blocking findings to the review: one whose files are unchanged keeps its verdict, and one whose files changed is judged again.

5. **Resolve the models (if the dispatch schema exposes a model parameter).**
   The choice is the user's, not the harness default.
   Ask once, name the two classes, then apply the answer to every dispatch in this review:

   ```text
   Subagent dispatch supports a model override.
   Inspectors and the runner work best on a small, fast model (e.g., `haiku`); every other role needs a strong one (e.g., `opus` or `sonnet`).
   Which models should I use for each class?
   ```

   A standard review uses only the strong class.
   If the user specified models earlier in the conversation, reuse them.
   Record the answer with `update-review --review <review_id> --models "<strong: ...; small: ...>"`, so that a new session can find it.
   Do not silently default.

## Architecture Section — When to Include

The quality lens covers architecture only when warranted: add the architecture section of its template when any of these apply:

- **Pre-merge / pre-PR review**: reviewing a branch against its target base.
- **User mentions "merge"**: explicit or implicit signal that this change is about to land.
- **User explicitly requests** architectural review, design feedback, or similar.
- **Main agent judgment**: the change crosses module boundaries, introduces new abstractions, modifies public APIs, or otherwise has architectural surface.
  In this case, **confirm with the user before adding** the architecture section.
- **The change adds a state, variant, field, or case to a data structure that crosses a boundary**: a module's public interface, an API payload, a stored record, a queued message.
  This one overrides the pre-commit exemption below.
  A data structure is cheapest to correct in the change that first gets it wrong, and the change that gets it wrong is usually small and local.

Leave the architecture section out for pre-commit reviews of localized changes and bug fixes within a single module.

## Prompts and Context

Each subagent prompt is self-contained: it will not see this conversation.
`dispatch` gives each role only the part of the packet it needs, as line ranges in its input file:

| Role                                                                     | Packet ranges                                                                          |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| Quality lens or test adversary for a component, list builder             | the metadata, the changed-file list, its component's hunks, and the source of truth    |
| Quality lens or test adversary without a component, the other two lenses | the whole packet                                                                       |
| Challenger                                                               | the metadata, the hunks of the files its records' claims cite, and the source of truth |
| Inspector                                                                | its partition's files' hunks, and the source of truth                                  |
| Forms checker, hunter                                                    | the whole packet                                                                       |
| Keeper, consolidator, runner, synthesizer                                | none                                                                                   |

Every role that reads the packet sets `read_through` to the last line it read, and `submit` sends it back for the rest when that line falls short of its ranges.

Prompt caching discounts only a byte-identical prefix.
The script fills each template's fixed slots from the review's values, the same way for every dispatch of that role, so the variable part is only the `## Input` slot at the end; do not edit a filled prompt.
Dispatch the first prompt of a batch, then the rest, so the later prompts find the cached prefix.
Prompts share a cache only when they run on the same model with the same subagent type.

## Components

A component is a set of changed files that one subagent reads together: files that call each other, or that the same tests cover.
A long diff dilutes a line-by-line read, so a change with more than one component gets one quality lens and one test adversary for each (`dispatch quality-lens --component <name>`, `dispatch test-adversary --component <name>`).

- In a standard review, you name the components.
  Keep the change as one component unless it has parts that do not depend on each other, and then divide it into at most three.
  The first dispatch for a component gives its files (`--component <name> --paths <file>...`); later dispatches give only `--component <name>`.
  Each changed file is in one component, and `status` names the changed files that are not in any.
- In a deep review, the components are those of the list builders (`deep-review.md`, Step A).

With one component, do not name it: dispatch `quality-lens` and `test-adversary` without `--component`, and each reads the whole packet.

## Lenses and Test Adversary

These roles read the change once, at the start of the review; the synthesizer's `dispatch` refuses until each has run.
`dispatch` with no role registers all of them.
Do not add prior findings, prior verdicts, edges to probe, or notes from earlier runs to any of their prompts.

- **Quality lens.**
  It reads the diff line by line for defects such as an off-by-one, a wrong operator, or a wrong default.
  Test adequacy belongs to the test adversary.
  With one component, a lens dispatched with `--component` does not stand in for the lens that reads the whole packet.
  When the architecture section applies, give `start-review` `--architecture yes`; the script then adds the section and the three tests from `data-representation.md` to the prompt, because subagents cannot invoke skills.
  With several components, the architecture section goes on one more quality lens without a component, because issues that cross modules need the whole packet; the script leaves it out of the per-component lenses.
- **Spec lens.**
  Dispatch it only when the packet reports `has_source_of_truth: true` or the review names a spec (`--spec`); `dispatch` with no role registers it in those cases, and `dispatch spec-lens` refuses in every other.
  With neither, the packet does not hold a spec or a stated intent to check against; skip the lens and say so in the report.
  If a spec or an intent exists, rebuild the packet with `--intent`/`--include` and start the review from it, or name a spec outside the packet with `--spec`, instead of skipping the lens.
- **Security lens.**
  Always dispatched.
  It covers the whole change, including dependency, logging, and configuration changes, in one dispatch, because an attack path can run from input in one component to a sink in another.
  Before `start-review`, copy the **Review Checklist** section of each `securing-code` tier3 reference whose domain the change implements into one file under `$TMPDIR`, and pass it as `--domain-checks-file`: `tier3-database.md` for queries and persistence, `tier3-file-upload.md` for accepting files, `tier3-input-validation.md` for parsing or validating untrusted input, `tier3-error-handling.md` for error paths that reach a user or a log, `tier3-memory-safety.md` for unmanaged memory, and `tier3-language-specific.md` for the change's language.
  Copy only the checklist items that apply to this kind of software.
  If a domain does not match, or the `securing-code` skill is not installed, do not pass a file; the OWASP checklist in the template still applies.
- **Test adversary.**
  It lists the behaviors the change adds or alters and finds the tests that cover them.
  It looks for three things: a behavior or path that does not have a test, a test that a wrong implementation would still pass, and a test whose expected result disagrees with the spec.
  For each one it writes a distinguishing input and runs it against the real code.
  A wrong result is a claim of a defect; a right result that a test does not check is a test gap.
  Its records keep the verdicts of its own runs.

## Consolidator

Dispatch the consolidator (`dispatch consolidator`) once `pending.consolidate` lists records.
It marks each record that is the same defect as another (the same operation and the same kind of input, judged by meaning) as a duplicate of that record, its **primary**, and puts every other record into one **failure mode**: a name, and a description of the mechanism that holds at any site.
Each claim proposes a failure mode; the consolidator decides.
It never rewrites a record: claims stay as their finders wrote them, and each record got its id when its finder's `submit` ran.
A duplicate is reported in the Dropped section, under the record it repeats.

## Challenger

Dispatch the challenger for `pending.challenge` (`dispatch` with no role gives each challenger at most twelve records).
It gets every record that a run did not settle:

- a record without an input;
- a record whose run was `not runnable`;
- a record that a run confirmed against an expected result that does not cite a source;
- in a standard review, which does not dispatch a runner, every record that has an input and was not run.

As devil's advocate, it argues the author's side and returns `upheld`, `disputed`, or `refuted`, with the strength of its evidence, and a revised priority when the claim's is wrong.
Its verdict decides the record.
It does not search for new defects: it has read every finding, so its search would start from them.
Its `review_critique`, where it says the review leans too hard or too soft, goes to the synthesizer.

The challenger also returns `disputed` when a verdict depends on author intent that the stated intent and the spec do not settle, and its argument states the question for the user.
A `disputed` finding goes into the report with both arguments.
`pending.rule` lists the disputed records of critical or high priority, whether or not this change introduced them: only those could change merge readiness, so only those wait for the user.
When only the synthesizer is left, `next` names them and the `rule` command, `dispatch` with no role does not register anything, and its `rulings` gives each one's claim and the challenger's argument: show these to the user, ask for each ruling, and record it with `review_state.py rule <record_id> --review <review_id> --verdict upheld|refuted --reason <the user's answer>`.
To report a record as disputed without a ruling, run `dispatch synthesizer` yourself.

## Synthesis

Dispatch the synthesizer (`dispatch synthesizer --report <report path>`, with the report path from `SKILL.md` Step 2).
`dispatch` with no role takes `--report` too; without it, the synthesizer writes `code-review-<YYYY-MM-DD-HHMMSS>-<scope>.md` (UTC) in the review directory.
`dispatch` refuses while any dispatch is open, while any record lacks a verdict, and while any step before synthesis has work waiting in `pending`.
The synthesizer's input holds every record in its section (findings, disputed, test gaps, dropped), each finding's blocking, confidence, and corroboration, the failure modes with their descriptions, the checks run before the review and merge readiness, each lens's summary, the challengers' review critiques, and this branch's previous review; in a deep review it also holds what each hunter searched, the inspections, the changes to the partition list, and the convergence counts.
The script computes the deterministic parts:

- **Blocking**: a confirmed or upheld finding of critical or high priority (after any revision the challenger made), unless the diff did not introduce it (`introduced: pre-existing`) or a real caller cannot produce its input (`reachable: no`).
- **Confidence**: high when a run confirmed it, or the challenger upheld it with strong evidence; medium when upheld with moderate evidence; low otherwise.
- **Corroboration**: a finding is corroborated when more than one dispatch found it (the record and its duplicates); `roles` lists the roles those dispatches ran.
- **Merge readiness**: `no` when a finding blocks, including a previous review's blocking finding whose files are unchanged; `unverified` when a check did not run, when the user went ahead despite a failing check, or when the previous review's records were deleted so its blocking findings could not be checked; `yes` otherwise.

The synthesizer groups and writes the findings by failure mode, reports each of the previous review's blocking findings as still open or judged again, and reports each disputed record that the user did not rule on, with its question, in the Disputed section.
Its `submit` refuses a report that leaves a record unnamed.

## Report

Present the report as `SKILL.md` Step 2 describes; submitting the synthesizer's report already recorded the finished review in the state.
The report has:

- A header, which the synthesizer writes, with the scope, base and head, the packet path, the date, the depth, whether the spec lens ran, and the coverage.
  For a standard review, the coverage says that the lenses and the test adversary read the change and a challenger judged their claims.
  For a deep review, it says how many partitions this review inspected, and why (first review, files changed, new input forms, or new partitions), and whether the loop stopped for convergence, and after which round.
- The merge readiness line, then the prioritized findings, grouped by failure mode.
- A **Disputed** section, a **Test gaps** section, a **Checks** section, a **Lenses** section, and a **Dropped** section; in a deep review, also a **Partitions** appendix.
- A **Previous review** section on a later review.
- Without a subagent tool, a line stating that the roles ran in one context (give `start-review` `--one-context yes`).

## Without a Subagent Tool

Run each role yourself, in the order of the review's steps, through the same `dispatch` and `submit` commands, reading each prompt from its `prompt_path`.
Give `start-review` `--one-context yes`.
`deep-review.md` adds two rules for the order of a deep review's roles.

## Dispatch Call Shape

This is an example - you may have a different API surface.
Defer to the subagent tool schema available in the current runtime/harness.

```text
Agent({
  description: "Security lens",
  subagent_type: "general-purpose",
  model: "<strong_model>",
  prompt: "Read the file <the security lens's prompt_path> in full and follow it exactly. It is your complete assignment.",
})
```

## Common Mistakes

- **Skipping intent clarification.**
  Subagents cannot ask the user; missing intent = guesswork at best, wasted dispatch at worst.
- **Doing review work in the orchestrator.**
  Judging, grouping, and synthesis belong to their roles; the orchestrator dispatches, and the script routes.
- **Reading or relaying role output.**
  Each role reads its input file and the script records its output; the orchestrator reads only command output and the final report.
- **Letting subagents edit code.**
  They write only their output file, and probes under `$TMPDIR`.
- **Inheriting the conversation.**
  A role that sees this conversation sees earlier findings; give every dispatch a fresh context.
- **Carrying the review in the conversation.**
  Every turn re-reads the whole conversation, so a ledger of dispatches or a long `status` printout is paid for again on each later turn; the state is on disk, and `dispatch` prints only what the next turn needs.
- **Exceeding the concurrency limit.**
  Batch in rounds of at most 8, or the harness's limit.
- **Adding the architecture section by default.**
  It's conditional — see "Architecture Section — When to Include" above.
- **Dispatching without resolving the models.**
  If the harness exposes model selection, silent defaulting hides a cost/quality decision from the user.
  Ask once, reuse across all dispatches.
- **Skipping the security lens.**
  It is always dispatched.
- **Asking the challenger for missed issues.**
  It has read every finding, so its search would start from them; discovery belongs to the finders.
- **Treating the challenger as authoritative beyond its batch.**
  It decides only the records it was given; a `disputed` finding goes to the user, not to a silent drop.
- **Dispatching a role again to recover a lost dispatch.**
  A dispatch that never recorded is still open; dispatch the subagent again with its own input file.
  Running `dispatch` again returns the same open dispatch, not a new one.
- **Writing scratch files into the review directory.**
  Helper scripts and notes are fine where the harness works that way, but they go under `$TMPDIR`; the review directory holds only what `review_state.py` and the roles write, the filled prompts, and the reports.
  Never keep a second ledger of verdicts: `status --review` is the record, and a copy can disagree with it.
- **Editing the state or review files by hand.**
  Only `review_state.py` writes them; a hand edit loses inspections and records.
- **Forgetting the extended-thinking phrase.**
  It engages extended thinking where the harness has one; omitting it leaves quality on the table.
