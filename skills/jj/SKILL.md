---
name: jj
description: |-
  Use when the repository uses Jujutsu (jj): a `.jj` directory sits at the repo root, `jj root` succeeds, or the user mentions jj, jujutsu, bookmarks, change IDs, or the op log. Also use when the user asks to explain or teach jj as the work happens. Not for plain git repositories, and not inside a harness git worktree that has no `.jj` directory.
---

# jj

Use Jujutsu well in a colocated jj and git repository, and when teach mode is on, explain each jj action in the final message of the turn so the human learns the flow and the raw commands.

## When to Use

- The repo has a `.jj` directory at its root, or `jj root` succeeds.
- The user names jj, jujutsu, a bookmark, a change ID, or the op log.
- The user asks to be shown or taught how jj is being used ("explain your jj", "teach me jj as you go").
- The user asks to set up jj in a repo, or to check whether jj is set up.

## When Not to Use

- A plain git repository with no `.jj` directory: use git.
- A harness git worktree of a colocated repo: it has `.git` but no `.jj`, so jj commands fail there.
  Use git in that worktree, and tell the user that jj is unavailable in it.
- Drafting the commit message text itself: use the `commit-message` skill when it is available, then apply the message with `jj describe -m`.

## Invocation Notice

- Tell the user when this skill is running: `jj`.
  Skip the notice when the user asked for the skill by name or slash command; spelling and spacing need not match.
  A phrase from this skill's own trigger list is not a name — naming the work is not naming the skill.

## Critical Constraints

These admit no exceptions.
"This case is different" does not license skipping one.

- Agents never push.
  `jj git push` is the human's command.
  The agent prepares the stack and hands it over.
- Never rewrite a change that is reachable from a remote bookmark.
  Before `squash --into`, `rebase`, `describe -r`, or `abandon` on any revision other than `@`, run the guard: `jj log -r '(<targets>) & ::remote_bookmarks()' --no-graph -T 'change_id.short() ++ "\n"'`.
  Non-empty output means the fix goes on top as a new change instead.
- Never write into a change the agent did not create this session.
  The human's changes are read-only.
  The agent's own changes are exactly `<base>..@`, where `base` is the change the preflight reported at Orient.
  Every command that selects changes to rewrite (`absorb --into`, `sign -r`, the finalize checks) uses that range, never authorship, because the agent and the human share one author.
- Never run `jj undo` or `jj op restore` without first reading `jj op log -n 5` and confirming the top operation is the agent's own.
  Never run either while another workspace is live.
  Prefer `jj op revert <op>`.
- Never `jj abandon` anything but the agent's own changes from this session.
  Abandon drops the content; it does not fold it into the parent.
- Never run a command that opens an editor or a TUI.
  Pass `-m` to `new`, `describe`, `commit`, `split`, and `squash`.
  Never run `jj squash -i`, `jj diffedit`, bare `jj resolve`, or `jj split` without paths.
  Run every jj command with `--no-pager --color=never` and with `JJ_EDITOR=false` in the environment so a missed `-m` fails instead of hanging.
- Never run git commands that move HEAD or the index in a colocated repo (`git commit`, `checkout`, `switch`, `reset`, `stash`, `rebase`, `merge`).
  Read-only git (`git log`, `git diff`, `git blame`) is fine.
- Never change jj config at user, repo, or workspace scope, and never use `--ignore-immutable`.
  Per-command `--config` and `--config-file` are allowed.
- Never perform setup.
  When a setup item is missing, walk the human through `references/setup.md`; do not run its steps.
- Never delete `.jj` or `.git`.

## Teach Mode

Teach mode is on when either holds:

- The user asks, in this session, to explain, show, or teach jj as the work happens.
- A project instruction file (`AGENTS.md`, `CLAUDE.md`, or `CLAUDE.local.md` at the repo root) contains a line that reads exactly `jj: teach`.
  The preflight script reports this.

When teach mode is on, read `references/teach.md` before the first jj command of the turn and follow it.
It adds a jj section to the final message of every turn and a short plan block at each confirmation stop.
It never adds commentary mid-turn.

When teach mode is off, the final message names each change the turn created or modified, one line each (change ID, description), and nothing more about jj.

## Confirmation Stops

The agent stops and waits for the human at these points and no others.
In teach mode each stop carries a plan block; teach mode never adds a stop.

- Orient, when `@` holds edits with no description.
- Before any `jj rebase`.
- Before `jj abandon` of anything other than a spike `@` the agent created this turn.
- A conflict whose resolution the agent cannot justify from the descriptions and specs (`references/recovery.md`).
- Finalize, before the final descriptions are applied.

## Workflow

The loop is Orient, Start, Work, Finalize, Recover.
Recover is entered from any phase.

### Orient

Run at the start of every turn that will use jj.

1. Run `scripts/jj_preflight.py` from the repo.
   Read the JSON on stdout.
   It reports the jj version, colocation, identity, the agent signing config, the immutability and conflict-marker settings, the teach flag, the state of `@`, the base of the agent's stack, the nearest bookmarks, the trunk, the workspace, and the current operation ID.
2. Keep `op_id`, `base`, and `workspace`.
   The operation ID is the turn's start marker for `scripts/jj_turn_log.py`; `base` bounds every revset over the agent's own changes; `workspace` filters the turn log.
3. If the status is `not-a-jj-repo`, stop and tell the user jj does not apply here.
4. If the status is `setup-required`, stop.
   Read `references/setup.md` and walk the user through the failed items.
   Do not run them.
5. If the status is `decision-required`, `@` holds edits with no description.
   Stop and report the file list from the preflight output.
   Offer to close the in-flight work in the repo's current native way: `jj describe -m` then `jj new` in a jj repo, or the repo's git commit convention if it is mid-conversion.
   Wait for the answer.
6. Warnings do not stop the turn.
   Report them once in the final message.

### Start

- If `@` is empty and has no description, describe it: `jj describe -m "<intent>"`.
- Otherwise start a new change on top: `jj new -m "<intent>"`.
- Write the intent in the repo's commit-message convention.
  A provisional one-line intent is enough during Work; the final wording is set at Finalize.

### Work

- Edit files. jj records them into `@` at the next jj command.
  Run `jj st` when a logical step is done, before any destructive filesystem or git command, and before handing control back.
- One change per logical step.
  When a step is done and its checks pass, start the next with `jj new -m "<next intent>"`.
  Build history forward; do not pile a turn into one change and carve it later.
- A fix that belongs to an earlier step of this turn: run the rewrite guard, then `jj squash --into <rev> -u <paths>` (keeps that change's message) or `jj absorb --into '<base>..@'` (read its output; it names every revision it rewrote).
  Never run `jj absorb` without `--into`; its default target is every mutable change, including the human's.
- A throwaway attempt: `jj new` with no message on top of the described change, try it, then `jj squash -u` to keep or `jj abandon @` to drop.
  Name this in the final message as a spike.
- A rebase (for example onto a moved trunk) or an abandon of anything other than a spike `@` is a confirmation stop.
  State the command and the reason, then wait.
- Do not use `jj edit` on any change.
  It moves the files on disk and redirects later edits into an old change.
- Conflicts: follow `references/recovery.md`.
  Resolve what the descriptions on both sides and the specs justify; escalate the rest.

### Finalize

Read `references/finalize.md` and follow it.
In short: snapshot, run the rewrite guard over `<base>..@`, run the repo's hooks explicitly because jj runs none, confirm no conflicts, present the stack with its descriptions and a diff summary, offer to squash it coarser, wait for approval, set the final descriptions, sign `<base>..@` with the agent config, and hand over.
The human pushes.

### Recover

Read `references/recovery.md` when something went wrong: a wrong squash, a lost file, a divergent change, a conflict, a stale workspace.
The op log is the undo history; read it before acting on it.

## Parallel Agents

One agent per working copy.
For several agents on one repo, read `references/workspaces.md`: one jj workspace per agent, created one at a time, with the hook detour for workspaces that have no `.git`.

## Output

- Code changes recorded as described jj changes, one per logical step, with the human's own changes untouched.
- A final message that lists the changes created or modified and, in teach mode, the jj section from `assets/turn-report.md` before the normal turn summary.
- No pushes, no config edits, no setup steps run by the agent.

## References

- `references/commands.md`: intent, command, git analogue, verified on jj 0.41; renamed and removed commands.
- `references/teach.md`: teach mode, the report, the concept table for git users.
- `references/finalize.md`: the finalize gate step by step, and what the human does to push.
- `references/recovery.md`: op log, undo, revert, restore, conflicts, divergent changes.
- `references/workspaces.md`: parallel agents in jj workspaces.
- `references/setup.md`: the human's checklist for a colocated repo and the agent signing config.
- `assets/turn-report.md`: the jj section template for the final message.
- `scripts/jj_preflight.py`: Orient checks.
  `scripts/jj_turn_log.py`: the turn's jj commands from the op log.
