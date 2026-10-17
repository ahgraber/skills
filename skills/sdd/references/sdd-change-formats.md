---
name: sdd-change-formats
description: SDD change artifact formats — proposal, design, tasks, and the cross-change ORDER.md — and the rules for changing specs during implementation. Referenced by sdd-propose, sdd-derive, sdd-apply, sdd-verify, sdd-sync, and sdd-archive.
---

# SDD Change Formats

Format reference for change directory artifacts.

## 1. Proposal Format

Location: `.specs/changes/<name>/proposal.md`

```markdown
# Proposal: {Change Name}

## Intent

{2-4 sentences describing why this change is needed and what problem it solves.}

## User Stories

### Story: {story-slug}

As a {role}, I want {goal}, so that {value}.

## Scope

**In scope:**

- {item}

**Out of scope:**

- {item}

## Approach

{High-level technical direction and strategy for implementing this change.}

## Open Questions

- {Unresolved decision or question that must be answered before implementation}

## Resolved Questions

- {YYYY-MM-DD} {question or requirement change}: {decision}. Decided with the user.
```

Rules:

- Intent is the "why" — not the "what" or "how"
- User Stories name the cross-cutting product value this change delivers — see § 1.1
- Scope prevents scope creep — be explicit about boundaries
- Open Questions is optional — omit if there are none
- Resolved Questions is optional.
  It records decisions made with the user, including requirement changes approved during implementation (§ 5.2).
  Each line carries the date of the decision and the words "Decided with the user".
- **Approach** is the draft sandbox for mechanism thinking during spec authoring.
  Early algorithm, heuristic, or strategy ideas that surface while writing the contract belong here until they are formalized into `design.md`.
  This keeps mechanism out of `spec.md` without losing the thinking.

### 1.1 User stories and the value ceiling

A **user story** is a cross-cutting slice of product value — the user-facing reason a change exists, in the form _As a {role}, I want {goal}, so that {value}_.
Keep the "so that {value}" clause: it is the point of the story, not decoration.
A story typically spans several capabilities, so it is **not** a contract — give it no scenarios.
Its serving requirements carry the contract; the story carries the value.

**Ladder to the north star.**
Every story should ladder up to the product north star at `<SPECS_ROOT>/NORTH-STAR.md` (the product elevator pitch — a durable, project-global singleton).
A change whose stories don't connect to the north star is drifting from product intent; surface that rather than proceeding.

**`Serves:` backlinks (M:N).**
Each delta-spec requirement that advances a story carries a `Serves: {story-slug}` line (see `sdd-spec-formats.md` § 4).
The relationship is many-to-many: one story is served by many requirements; one requirement (e.g., a shared auth check) may serve many stories.

**The value ceiling.**
The story bounds effort.
`sdd-apply` implements only to the depth a served story requires; `sdd-verify` flags a requirement, scenario, or implementation that serves no story as a WARNING — suspected over-engineering, _out of scope by construction_.
This is the counterweight to SDD's thoroughness machinery (partition coverage, write-site enumeration): granularity is justified only to the extent a user story needs it.

**Lifecycle — change-scoped, not durable.**
User stories live here in `proposal.md`, and `Serves:` backlinks live only in delta specs.
Both are disposable: `sdd-sync` strips `Serves:` lines when merging deltas into baseline (like the `> Previously:` line), and the proposal is archived with the change.
Baseline specs stay value-free.
The value layer lives where the work happens — the active change — without committing to a durable story tier.

## 2. Design Format

`design.md` is the **legitimate home for mechanism** — chosen algorithms, heuristics, thresholds, data structures, strategies, retry policies, model choices, similarity metrics, and architectural decisions.
If a draft spec sentence names one of these, it probably belongs here rather than in `spec.md`.
See `sdd-spec-formats.md` § 1.3 for the spec/design/tasks responsibility split.

Location: `.specs/changes/<name>/design.md`

````markdown
# Design: {Change Name}

## Context

{Background, constraints, and assumptions that shape this design.}

## Decisions

### Decision: {DecisionName}

**Chosen:** {the selected approach}

**Rationale:** {why this approach was chosen}

**Alternatives considered:**

- {alternative}: {why it was not chosen}

## Architecture

{ASCII diagram or prose description of component relationships and data flows.}

```text
{optional ASCII art}
```

## Risks

- **{Risk}**: {mitigation strategy}

## Verification Waivers

- **Requirement:** {requirement name or ID}
  **Reason:** {why automated execution evidence is not feasible — e.g., requires production data, third-party sandbox unavailable, manual operator step}
  **Manual evidence:** {path to captured output, runbook reference, screenshot, or commit where manual verification was recorded}
  **Recorded:** {ISO date or commit SHA when this waiver was first added — used by sdd-verify's provenance check}

## Spec Changes

- **Change:** {capability}: {imperative description, e.g. "add scenario for a token that expires during refresh"}
  **Source:** {upstream: the story, requirement, or decision it follows from | agent choice | rebase onto {change-name}}
  **Rationale:** {why the spec should say this, stated without reference to what the code currently does}
  **Approved by user:** {ISO date | pending}

## Baseline Errors

- **Spec:** {capability and requirement in `.specs/specs/`}
  **Error:** {what the baseline states wrongly}
  **Fix:** {the corrected text or behavior}

## Verification Overrides

- **Finding:** {exact verify finding or stable identifier}
  **Stage:** {workflow stage where the override was applied — usually `verify`, sometimes `sync`}
  **Reason:** {why work must proceed despite the unresolved blocking finding}
  **Constraints:** {what is still forbidden — e.g., no ignore, no suppression, must wait for upstream release}
  **Follow-up task:** {exact unchecked task text or task reference in `tasks.md`}
  **Approved by:** {who explicitly authorized the override — typically `user`}
  **Recorded:** {ISO date or commit SHA when this override was first added}
````

The `## Verification Waivers` section is optional and only present when one or more SHALL requirements cannot be covered by runnable evidence (test, schema check, or captured output).
`sdd-verify` flags any unwaived SHALL without runnable evidence as CRITICAL, and a waiver entry without a checkable manual evidence reference is itself CRITICAL.
The `Recorded` field is required for the provenance check; if absent, `sdd-verify` falls back to `git blame`.

The `## Spec Changes` and `## Baseline Errors` sections are optional.
They record spec edits made during implementation; § 5 defines when each is used.

The `## Verification Overrides` section is optional.
User overrides of otherwise blocking findings or gate outcomes are permitted, but they must be recorded in the change artifacts to preserve an audit trail across design, implementation, verify, and sync.
An override does not remove the finding or change its severity; it only records that work proceeded despite the blocker.
Each override must identify what was overridden, where in the workflow the intervention happened, why work continued, what remained forbidden, who approved it, and what follow-up work stayed open.

## 3. Tasks Format

Location: `.specs/changes/<name>/tasks.md`

```markdown
# Tasks: {Change Name}

## {Group Name}

- [ ] {Concrete, atomic implementation step}
- [ ] {Concrete, atomic implementation step}

## {Another Group Name}

- [ ] {Concrete, atomic implementation step}
- [x] {Completed implementation step}
```

Rules:

- Tasks are atomic — each task is a single, completable unit of work
- Tasks describe implementation actions, not outcomes (the outcomes live in `spec.md`)
- Groups organize by component or phase (e.g., 'Backend', 'Frontend', 'Tests')
- Use `- [x]` to mark completed tasks
- If a blocking verify finding or gate outcome is explicitly overridden, keep or add an unchecked remediation task in `tasks.md` that names the fix still required.
- Every SHALL requirement in the delta specs must be backed by at least one task that produces runnable evidence — a named test (unit, integration, or e2e), a schema-snapshot check, or a captured-output step.
  Requirements that genuinely cannot be tested automatically belong in `design.md` § Verification Waivers instead.
  `sdd-verify` enforces this rule and will flag uncovered SHALL requirements as CRITICAL.
- Every **contract-relevant write-site** (see § 3.1) for a SHALL requirement must be paired with an evidence-producing test task that exercises the contract _through that write-site_.
  When a new write-site emerges during implementation (e.g., a dedup shortcut, retry path, cache fast-path, fallback branch), `sdd-apply` adds the paired test task before the implementation task is marked complete.

### 3.1 Contract-relevant write-sites

A **contract-relevant write-site** is a code location that produces or modifies a value the spec asserts a SHALL contract over.

When the implementation has multiple such locations for the same contract — for example, a canonical write path _and_ a deduplication shortcut, or a primary handler _and_ a retry path — each is a contract-relevant write-site, and each requires its own evidence-producing test task.
A single test exercising one path leaves the other arms of the contract unverified.

Identifying write-sites is mechanism-level work and lives in tasks (and verify), not in specs.
Specs partition along _semantic_ states the contract holds in (see `sdd-spec-formats.md` § 1.6).
Tasks ensure each _implementation path_ producing those states is exercised.

**Heuristic for spotting them:**

- Multiple call sites that mutate the same persisted field.
- Branches with early `return` that bypass the canonical path (shortcuts, caches, idempotency fast-paths).
- Retry, fallback, or compensation paths that re-enter the same write logic.
- Merge or composition steps that combine fields written by other sites.

**What is _not_ a contract-relevant write-site:**

- Internal helpers that don't produce a contract-asserted value on their own.
- Pure transformations whose output is consumed by exactly one canonical write-site.
- Logging, metrics, or instrumentation calls that don't affect contract-asserted state.

## 4. Implementation Ordering

Implementer-facing lists in change artifacts — affected capabilities in `proposal.md`, decisions in `design.md`, task groups and tasks in `tasks.md` — must be ordered so each item depends only on items earlier in the list.
The implementer should always be building _on_ a capability already present, never _in anticipation of_ one.

Apply in priority order:

- Contract-defining work (schemas, type/model definitions, interfaces) before consumers.
- Foundation capabilities before composite ones — primitives before what combines them.
- Side-effect-free units (pure helpers, validators) before stateful units (persistence, network, scheduling).
- Tests paired with or immediately after the unit they exercise — never before it exists.
- Independent items: any internal order is fine, but mark the group as independent so the implementer can reorder or parallelize safely.

Alphabetical and "order of discussion" are not acceptable defaults — they ignore the implementer's experience.

### 4.1 Worked example

A change adding token-based auth:

1. Token model and storage schema _(contract)_
2. Token issuance — sign + persist _(depends on 1)_
3. Token validation — verify + lookup _(depends on 1)_
4. `/login` endpoint _(depends on 2)_
5. Auth middleware on protected routes _(depends on 3)_

Alphabetical order would force the implementer to scaffold middleware against a missing token contract, then rewrite when it lands.

### 4.2 Cycles

If two items each appear to require the other, the cycle is usually a sign that one needs to split.
Surface it to the user rather than picking arbitrarily.

## 5. Spec Changes During Implementation

Specs are the source of truth during implementation.
When implementation or testing conflicts with a spec, change the code to match the spec.
Change the spec only as § 5.1 or § 5.2 allows.

Change the code, not the spec, when the spec text traces to a user story, the north star, or a recorded user decision.
Change the code, not the spec, when the only support for the code's behavior is its own tests.

`tasks.md` and `design.md` are working documents.
Add, reorder, or replace tasks as the work requires.
Change a design decision when implementation shows a better choice, and update its Decision entry (Chosen, Rationale, Alternatives).
A design decision that traces to a user decision is the exception: changing it is a requirement change (§ 5.2).

### 5.1 Scenario changes

The implementer may add a scenario, or revise one, without asking the user first.
A scenario change must meet both of these conditions:

- It does not narrow what its requirement guarantees.
  A revision that adds an exception, a precondition, or a weaker outcome is a requirement change (§ 5.2).
- Its rationale is something other than what the code currently does.

Record each scenario change in `design.md` § Spec Changes (§ 2) with `Approved by user: pending`.
Set **Source** to the story, requirement, or decision the scenario follows from.
When the spec was silent and the implementer picked the behavior, set **Source** to `agent choice`.
An agent-choice scenario often describes what the code already does, so the user must read it most closely.

At the end of each turn that changed scenarios, list the changes for the user, grouped by source, and ask for approval.
When the user approves, replace `pending` with the date.

If one turn produces 5 or more agent-choice scenarios, stop and ask the user before continuing.
That many silent spots usually means the spec is underspecified, and the user should decide the missing behavior.

### 5.2 Requirement changes

A requirement change is any of these:

- Adding, removing, or rewording a requirement.
- A scenario revision that narrows what its requirement guarantees.
- A breaking change.
- A change that touches the proposal's Out of scope or Resolved Questions.
- A change to a design decision that traces to a user decision.

Get the user's approval before implementing a requirement change.
Record it in the same commit as the code:

- A `design.md` Decision entry (Chosen, Rationale, Alternatives).
- A dated line in the proposal's Resolved Questions that ends "Decided with the user".

If the change raises what every implementation of an extension point must guarantee (every backend, store, or plugin), also add a contract test that runs against each declared implementation.

When an implementation change forces a spec edit but no caller or operator could observe a difference, the spec was pinning mechanism (`sdd-spec-formats.md` § 1.4).
Do not update the method name the sentence mentions.
Propose a rewrite that states the outcome the sentence protects; the rewrite is a requirement change, so it goes to the user.

### 5.3 Baseline errors

An error found in a baseline spec (`.specs/specs/`) during implementation is not part of the change.
Do not edit the baseline during implementation.
Record the error in `design.md` § Baseline Errors (§ 2).
`sdd-sync` fixes recorded baseline errors after the user confirms them, and reports them separately from the change's own edits.

### 5.4 Commits that edit spec text

A commit that edits spec text lists each spec change in its body, one line per change.
Write each line in the imperative, in plain language, prefixed with the capability:

```text
auth: add scenario for a token that expires during refresh
auth: require re-authentication after a password change
```

The line names what changed.
The rationale and the user's approval stay in `design.md` and the proposal.
With this convention, `git log -- .specs/` reads as a log of spec decisions.

### 5.5 Spec-drift check

The spec-drift check finds every spec edit made since the proposal was committed, and confirms that each one has the record it needs.

1. Find the proposal commit: the first commit that added the change's `proposal.md`.

   ```bash
   git log --diff-filter=A --format=%H -- .specs/changes/<name>/proposal.md | tail -n 1
   ```

2. Diff the delta specs from that commit to the working tree:

   ```bash
   git diff <proposal-commit> -- .specs/changes/<name>/specs/
   ```

3. Classify each hunk as a scenario change (§ 5.1) or a requirement change (§ 5.2).

4. Check each hunk against its record:

   - A scenario change needs a `design.md` § Spec Changes entry with a dated `Approved by user` line.
   - A requirement change needs a `design.md` Decision entry and a dated Resolved Questions line.
   - A rebase onto another change's synced text (§ 6.2) needs a `design.md` § Spec Changes entry whose **Source** names that change, with a dated `Approved by user` line.

A hunk without its complete record blocks sync.
If no proposal commit exists, the check cannot run.
Report that, and do not treat the change as clean.

## 6. Change Order Format

Location: `.specs/changes/ORDER.md`

`ORDER.md` records the order in which active changes apply, and the reason for each constraint.
It is optional.
Create it when two or more active changes have an ordering dependency (§ 6.1) or share a requirement (§ 6.2).
It is a file, not a directory, so it is not an active change and it is never archived.
Delete it when the remaining active changes can apply and sync in any order.

The order is a graph, not a list.
Each change's **Starts after** entries are the constraints; the row order is one valid order among possibly several.
Two changes whose constraints are met can run in parallel.

### 6.1 Ordering dependencies

A change depends on another change when it cannot start `sdd-apply` until the other change reaches a gate.
Each dependency has one kind:

- **capability**: the later change uses behavior, a contract, or code that the earlier change adds or changes.
- **rework**: either order works, but one order makes a change redo work that the other change does, for example porting code that the other change then rewrites.
  Record the chosen order and what the other order costs.
- **spec text**: the two changes edit the same requirement (§ 6.2), and the later change copies the requirement only after the earlier change syncs.

A gate is one of these events of the earlier change:

| Gate       | Met when                                            |
| ---------- | --------------------------------------------------- |
| `proposed` | Its proposal commit exists.                         |
| `applied`  | Every task in its `tasks.md` is checked.            |
| `synced`   | Its delta specs are merged into the baseline specs. |

Use `synced` unless the later change needs the earlier change only as a proposal or as code.
A **spec text** dependency is always `synced`.
An archived change meets every gate, so remove it from `ORDER.md` (§ 6.5).

A dependency cycle means that one change must split.
Surface the cycle to the user (§ 4.2); do not record it.

### 6.2 Shared requirements

Two changes share a requirement when their delta specs name the same requirement in the same capability: both MODIFY or REMOVE it, one MODIFIES what the other ADDS, or one RENAMES the capability that the other edits.
`sdd-sync` replaces a MODIFIED requirement as a whole.
The change that syncs second therefore copied requirement text that is now out of date, and its sync silently reverts the first change's edit unless it copies the requirement again from the synced baseline.

Two changes that edit different requirements in the same capability do not share a requirement.
Sync preserves every requirement a delta does not name.

Changes that share a requirement can be ordered by a **spec text** dependency (§ 6.1), or left unordered and rebased by whichever change syncs second.
Both are valid; choose with the user.
List each shared requirement in `ORDER.md` in either case.
`sdd-sync` reports which changes must copy the requirement again after each sync.

Copying the requirement again is a **rebase**.
It edits the delta spec after the proposal commit, so the spec-drift check (§ 5.5) sees it.
Record each rebase in `design.md` § Spec Changes with **Source** set to `rebase onto {change-name}`, and get the user's approval.
If the two changes' edits conflict, the merged requirement is a requirement change (§ 5.2).

### 6.3 Template

```markdown
# Change Order

Last reviewed: {YYYY-MM-DD} ({event that prompted the review, e.g. "`token-refresh` archived"})

This file lists the active changes whose order matters, and why.
Refer to a change by its directory name, never by its position in a list.
Update this file when a change is proposed, archived, or reordered.
Delete this file when the remaining changes can apply and sync in any order.

## Sequence

| Change          | Starts after                                    |
| --------------- | ----------------------------------------------- |
| `{change-name}` | (none)                                          |
| `{change-name}` | `{change-name}` synced                          |
| `{change-name}` | `{change-name}` synced, `{change-name}` applied |

## Reasons

### `{change-name}`

- **After `{change-name}` ({capability | rework | spec text}):** {what this change needs from the earlier change, or what goes wrong in the other order.}

## Shared requirements

- `{capability}`: `{Requirement name}`: `{change-name}`, `{change-name}`.

## Not scheduled

| Change          | Starts when                                                      |
| --------------- | ---------------------------------------------------------------- |
| `{change-name}` | {external condition, e.g. "the user settles the open questions"} |

## Independent

- `{change-name}`
```

Omit any section that has no entries.

### 6.4 Rules

- Every active change directory appears in exactly one of `## Sequence`, `## Not scheduled`, or `## Independent`.
  A change that appears in none of them has not been assessed.

  - `## Sequence` holds each change that has a **Starts after** entry or is named in one.
  - `## Not scheduled` holds each change that waits for a condition outside the active changes, such as a user decision or an external release.
    Name the condition so that someone can check whether it is met.
  - `## Independent` holds every other change.
    A change that shares a requirement but has no **Starts after** entry goes here; `## Shared requirements` lists what it must rebase.

- Every change named in the file is an active change directory.
  An archived change does not appear, not even as a met prerequisite.

- Name each change by its exact directory name in backticks.
  Never refer to a change by position ("the third change", "the next one").

- Each `## Sequence` row comes after every change in its **Starts after** entry.

- Every **Starts after** entry has a matching bullet under `## Reasons`, with its kind from § 6.1.
  A **spec text** reason names each shared requirement as `{capability}`: `{Requirement name}`.

- `ORDER.md` records ordering only.
  Do not record a change's progress; read it from the change's own artifacts and the git history.
  Keep open questions, scope, and design in the change's own artifacts.
  A reason states what one change needs from another, not the full content of either change.

### 6.5 Maintenance

| Event                | Skill         | Update to `ORDER.md`                                                                                                                                                                  |
| -------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A change is proposed | `sdd-propose` | Assess the new change against every other active change (§ 6.1, § 6.2). Add the change to one section. Create the file when the first dependency or shared requirement appears.       |
| A change syncs       | `sdd-sync`    | No update. Report the changes whose **Starts after** entries are now all met, and the changes that share a requirement with the synced change.                                        |
| A change is archived | `sdd-archive` | Remove the change from every section. Remove each **Starts after** entry and **Reasons** bullet that names it. Remove each shared requirement line that names fewer than two changes. |
| Any update           | any           | Update **Last reviewed**. Delete the file when no **Starts after** entry, no shared requirement, and no `## Not scheduled` change remains.                                            |

Commit `ORDER.md` together with the change artifacts that caused the update.
