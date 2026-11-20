---
name: code-review
description: |-
  Use when reviewing code changes before committing or merging — staged diffs, branch diffs, or PR readiness checks. Triggers: 'review my code', 'check these changes', 'review this branch', 'give feedback on my diff', 'is this PR ready?'. Not for implementing features, running test suites, formatting-only passes, or building understanding of a change (use teach-me).
---

# Code Review

## Overview

Structured, actionable code review focused on correctness, bugs, style, and maintainability.
Act as a senior engineer: thorough, pragmatic, impact-first.

## When to Use

- Reviewing staged changes before committing.
- Reviewing branch changes before merging or opening a PR.
- Checking a diff for correctness, bugs, style, or structure.
- Final review of all changes on a feature branch.
- Quick sanity-check of a small changeset before pushing.

**When NOT to use:**

- Implementing new features from scratch.
- Running or repairing a test suite as the task itself (see `writing-tests` or equivalent).
- Refactoring without a prior review (review first, then refactor on request).
- Linting or formatting only — use a linter or formatter directly.

## Invocation Notice

- Tell the user when this skill is running: `code-review`.
  Skip the notice when the user asked for the skill by name or slash command; spelling and spacing need not match.
  A phrase from this skill's own trigger list is not a name — naming the work is not naming the skill.

## Constraints

- Do NOT modify code unless explicitly asked.
- Do NOT guess missing code or behavior; ask for missing context.
- Do NOT suggest adding suppressions (e.g., `#pragma warning disable`).
- Stay focused on review quality; avoid unrelated commentary.

## Common Mistakes

- **Reviewing without full context** — jumping to conclusions without reading the complete diff or understanding intent.
- **Mixing review and edits** — modifying code during the review phase instead of separating feedback from implementation.
- **Nitpick overload** — burying critical issues under dozens of style nitpicks.
- **Ignoring intent** — critiquing design choices without understanding the constraints or goals behind them.
- **Incomplete scope** — reviewing only one file when the change spans multiple files or modules.
- **Searching near the last defect** — a re-review that looks only at last review's findings and their neighbors finds one more failure mode per run; review the whole change again (a deep review starts from the partition list).

## Workflow

### Step 0 — Gate: Review Type, Scope, and Packet

**Review type.**
Decide it first; it decides what the rest of this step does.

- **Quick review**, only when the user asks for a "quick" or "sanity" check: follow `references/quick-review.md`.
  It does not use partitions, subagents, or review state.
- **Standard review**, in every other case unless the user asks for a deep one: follow `references/standard-review.md`.
  The lenses and the test adversary read the change and look for defects, and one challenger argues against what they claim.
  It takes about seven dispatches with one component; each further component, up to three, adds a quality lens and a test adversary, and each further twelve records to judge add a challenger.
- **Deep review**, only when the user asks for a "deep", "thorough", or "exhaustive" review: follow `references/deep-review.md`.
  It adds the partition list (an inspector for each partition, in rounds, and a forms checker), a probe run for each claim, and a hunter for each confirmed failure mode.
  It costs several times the dispatches of a standard review.

Do not choose a deep review for the user, and do not lower a deep review the user asked for: when a change crosses a security boundary or the user states that a missed defect is costly, say in one line that a deep review exists and what it adds.

**Scope.**
Identify whether this is a pre-commit or pre-merge review.
If the user does not specify scope, infer it from context:

- On a feature branch with commits ahead of the target base branch → pre-merge review (`branch` scope, `--base <ref>`).
- Staged changes present → pre-commit review (`staged` scope, `--staged`).
- Uncommitted changes the user wants reviewed as they stand → `worktree` scope (`--worktree`); it includes untracked files that git does not ignore.
  Every scope leaves out the `.verify/` directory of each SDD change, where `sdd-verify` keeps its run logs and reports.
- Ask if ambiguous, especially when default branch detection fails.

**Review directory (standard and deep reviews).**
Run `scripts/review_state.py status --scope <scope>`; it prints `review_dir`, `review_dir_in_repo`, `state_exists`, `pending.inspect` (the partitions waiting for inspection), and `previous_review`.
The review directory keeps one layout:

- At its top level: only the state file and its lock, the `.gitignore`, and the reports (`code-review-*.md`).
- In `reviews/<review_id>/`, which `start-review` creates: everything else this review writes, which is its records, the packet copy, the roles' input and output files, and the filled prompts (`prompts/`).
- Under `$TMPDIR`, never in the review directory: the packet as first built, probes, scratch scripts, caches, and build output.

A report path that the user, a brief, or project instructions name overrides the report's place.
Deleting a finished review's `reviews/<review_id>/` removes it completely and leaves the state and the reports intact.
`review_dir` is the main worktree's `.review/` when it exists, so every linked worktree shares one partition list; otherwise it is a directory under `$TMPDIR`.
To use another directory, such as when the sandbox does not allow writes to the main worktree, pass `--review-dir <path>` to `status` and to `start-review`; the script puts it in each `submit_command`, and you pass it to every later command.
When `review_dir_in_repo` is false, ask the user once per repo: "May I create `.review/` at the repo root for review files and state, with a `.gitignore` so git ignores it?"
If the user agrees, create `.review/` with a `.gitignore` that contains `*`, and run `status` again.
If the user declines, or the run cannot ask, continue in `$TMPDIR` and say in the report that a later session may not see this review's state.
Only `review_state.py` writes the state file and the review's records (`references/partition-discovery.md` § 6).

**Checks gate (every review type).**
Run the project's own checks before reviewing, and do not review code that fails them.

1. Run the project's hooks or linters (pre-commit, prek, or what CI runs) on the changed files, the fixing hooks included.
   If a hook changes a file, stop and show the user the change; the user keeps or reverts it, and for a staged review stages what they keep.
   The review starts only after that, so no one reads a file while a hook rewrites it.
2. Run the project's test suite to completion, so that every failure shows: when the runner stops at the first failure, give it the option that runs the rest (such as `cargo test --no-fail-fast`).
3. If a check fails, do not start the review: report the failures, and the user fixes them.
   Only the user can decide to review despite a failing check, such as a flaky test or a failure the base branch shares; merge readiness is then `unverified`.
   In a standard or deep review, pass that check to `start-review` with `--failed-checks` and the user's reason with `--reason`.
   The same holds for a check that cannot run, such as tests that need a service: only the user can decide to review without it, and you pass it with `--skipped-checks` and the user's reason with `--reason`.
   A check that the sandbox does not let you run has not failed: give the user the command, ask them to run it and share the result, and pass it with `--passed-checks` or `--failed-checks` by that result.
4. In a standard or deep review, pass the checks that passed to `start-review` with `--passed-checks`; when there are no checks to run, do not pass any, and merge readiness is `unverified`.
   A quick review lists each check and its result in its report.

**Build the review packet.**
Run `scripts/build_review_packet.py` to write one packet (diff, changed-file list, and source of truth) that every later step reads instead of re-deriving the base ref and re-running git:

```sh
mkdir -p "$TMPDIR/code-review"
scripts/build_review_packet.py --base <ref> \
  --out "$TMPDIR/code-review/review-packet-<YYYY-MM-DD-HHMMSS>.md" \
  --intent "<what this change is for>" --include <spec-or-plan-if-any> \
  > "$TMPDIR/code-review/review-packet-<YYYY-MM-DD-HHMMSS>.json"
```

Use `--staged` or `--worktree` instead of `--base` for those scopes.
Give `--include` once for each file, with an absolute path; a relative path resolves against the current directory, not the repository.
Always pass `--out`; without it the script writes into the repo whenever `.review/`, `._scratch/`, or `.scratch/` exists.
It prints JSON with `packet_path`, `has_source_of_truth`, `diff_truncated`, `index` (the line range of each section and of each file's hunks), `content` (each changed file's content id, which `review_state.py` checks against the files later), and `packet_tokens`.
For a standard or deep review, start the review from that JSON with `scripts/review_state.py start-review` (`references/review-dispatch.md`, "Prerequisites Before Dispatch", gives the command and its options).
Run it only after the intent is clarified with the user (Step 1; Prerequisites step 1 of that reference), because `--intent` fills every role's prompt and a repeated `start-review` with another intent is refused.
It copies the packet and its JSON into the review's directory, which every role then reads, and prints the `review_id` that every later command takes; it refuses a packet whose diff was truncated, because the roles would miss the changed lines past the cut; rebuild the packet with a larger `--max-diff-bytes`.
For a quick review of a truncated packet, read the rest of the diff from git.
The packet fixes _what changed_ so no one re-derives it; it is a floor, not a ceiling, and reviewers keep reading surrounding code, callers, history, and tests as the review demands.

**Source of truth.**
If `has_source_of_truth` is false, the packet is a bare diff: it carries neither a spec nor a stated intent.
A reviewer grading spec compliance from a bare diff will silently invent a spec and grade against it.
Ask the user for the intent and any spec (Step 1), and rebuild the packet with `--intent`/`--include`.
A spec that cannot go into the packet is named with `start-review --spec`, and the spec lens then runs against it.
If there is neither, review without the spec lens and say so in the report; never infer a spec from the diff and grade against it.

### Step 1 — Review (No Edits)

Run the review type set in Step 0.
Clarify author intent with the user before a standard or deep review dispatches anything; subagents have no conversation history.

### Step 2 — Report

Present the review as a prioritized list of issues.

**Check each suggested change.**
A suggested change that looks right has not been shown to work.
Before you present the report, check the suggested change of every blocking finding:

1. Show that it removes the defect: the changed code gives the finding's expected result on its distinguishing input.
   Run the input when the code can run; otherwise trace it through the changed code line by line.
2. Trace what the change touches next: the callers of the changed code, other code that reads the same data, the tests, and the spec.
   Name each new defect the change causes, or name what you checked.

State the result under the finding's suggested change, in the chat report and in the report file.
When a check cannot run, label the change unchecked and say what would check it.
Check a non-blocking finding's change the same way when the user asks for its fix.

**Persist the report.**
Write the full report to a file so it outlives the conversation and can be handed to another agent or to the `refactor` skill.
Write it in the review directory from Step 0 (for a quick review, beside the packet), unless the user, a brief, or project instructions (AGENTS.md, CLAUDE.md, or the equivalent) name another path.
In a standard or deep review the synthesizer writes it, at the path given to its dispatch with `--report`; when none is given, the script names it as below, in the review directory.
Do not create a repo directory other than `.review/`, and that one only through the question in Step 0; the user owns the repo layout.
Name the file `code-review-<YYYY-MM-DD-HHMMSS>-<scope-slug>.md`, so parallel runs do not collide.
Start it with the scope, base and head, the packet path, and the date, then the report as presented.
If the write fails, say so in chat; the chat report then is the only copy.

The file does not replace the chat report.

**The review state** (standard and deep reviews).
Submitting the synthesizer's report records the finished review in the state, so the next review on this branch finds it as `previous_review`, and the next `start-review` adds its blocking findings: a finding whose files are unchanged keeps its verdict, and one whose files changed is judged again.
The partition list, and each inspection of a deep review, were saved during the review; the state does not hold findings, because the next review's inspectors read it.
The findings stay in the review's own records, in its directory.

**Recommend a security scan.**
When the change touches a security boundary, recommend a dedicated security scan in one line.
A change touches a security boundary when it parses or classifies untrusted input, makes an authorization, sandbox, or policy decision, or handles secrets or credentials.
If the `security-scan` skill is available, offer it for the change; `security-deep-scan` scans only a whole repository or a path, so offer it only as a follow-up when the user needs exhaustive coverage of the code the change touches.
If neither is available, say that the change crosses a security boundary and that a dedicated security review is worth running; this review's security lens does not replace one.
Do not run a scan without the user's approval.

End with the prioritized issues, the report path, the depth of the review, and, for a deep review, the number of partitions inspected.

### Step 3 — Fixing Findings

Recommend that someone other than the reviewer fix the findings: the user, or a separate agent.
Implementer and reviewer roles work best kept separate, because a reviewer that fixes its own findings is then the one judging whether its fixes are complete.

If the user asks the reviewer to fix them anyway:

1. Apply only changes discussed in the review.
2. Make minimal, targeted edits.
3. Do not introduce additional refactors without user approval.
4. Run each fixed finding's distinguishing input against the changed code, then run the test suite.
   A fix counts as done only when the input gives the expected result and the suite passes.
5. After editing, summarize what changed and why, mapping back to the original review items, and recommend a fresh review of the fixes.

## Scope Note

Treat the recommendations in findings as preferred defaults.
When a default conflicts with project constraints, suggest a better-fit alternative, call out tradeoffs, and note compensating controls.

## References

Paths below are relative to this skill's directory; give scripts their full path when running them from the reviewed repository.

- `references/quick-review.md` — the quick review: triage, the areas to evaluate, rules, and findings.
- `references/standard-review.md` — the standard review's steps.
- `references/deep-review.md` — the deep review's steps: partitions, rounds, runners, hunters, and the forms checker.
- `references/review-dispatch.md` — what the standard and deep reviews share: the dispatch cycle, the prerequisites, the roles, and the report.
- `references/partition-discovery.md` — the partition list: origins, input forms, inspection, refinement, coverage, and review state.
- `references/glossary.md` — the words the standard and deep reviews use, each defined once.
- `scripts/review_state.py` — resolves the review directory, keeps the partition list, and keeps each standard or deep review's dispatches and records: `status`, `start-review`, `update-review`, `dispatch`, `submit`, `start-round`, `rule`, `schema`; each command that changes state is safe to repeat.
- `scripts/build_review_packet.py` — writes the review packet and its line index.
- `assets/prompt-*.md` — one prompt template per subagent role in the standard and deep reviews, which `review_state.py` fills; `assets/claim.md` — the fields of a claim, which `review_state.py submit` checks.
- `assets/deep-review-flow.svg` — the deep review's flow chart, rendered from `references/deep-review.md`.
- `assets/issue-template.md` — issue type/priority legends and suggestion format.
- `references/data-representation.md` — the data-shape tests: where to look, three tests, and the evidence each finding must carry.
- `references/review-best-practices-links.md` — external review best-practice links used by this skill.
- `references/git-diagnostics-before-review.md` — git commands for assessing codebase health before reviewing.
- `securing-code` skill (`references/tier2-review.md`, `references/tier3-*.md`) — OWASP-mapped security checklist for the security lens.
