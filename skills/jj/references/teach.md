# Teach mode

Teach mode explains the agent's jj usage so the human learns the flow and the raw commands.
It is a mode, not a default: it runs only when the user asks in the session or the project instruction file carries the line `jj: teach`.

## Where the explanation goes

Only two places.
Never mid-turn: text written while the work runs scrolls out of the human's view.

1. The final message of the turn, as a jj section placed before the normal turn summary.
   This is the main teaching channel.
2. A plan block at a confirmation stop.
   The stops are the ones `SKILL.md` defines under Confirmation Stops: the Orient decision on undescribed `@`, a rebase, an abandon other than a spike `@`, a conflict escalation, and the Finalize approval.
   At each, state what the next jj step is and why before asking.
   Teaching never adds a stop of its own.

## Producing the jj section

1. At the end of the turn, run `scripts/jj_turn_log.py --since <op> --workspace <workspace>` with the operation ID and workspace name that `jj_preflight.py` reported at Orient.
   It prints the jj commands recorded in this workspace since that operation, in order, with snapshots and read-only commands removed.
   This list is the record of what ran; do not write it from memory.
   The op log also records any jj command the human ran in the same workspace during the turn, so drop a line you did not run and say that you dropped it.
2. Group the commands by phase: Start, Work, Finalize, Recover.
   Use the headings only for phases that ran.
3. For each command, write one line in the shape of `assets/turn-report.md`: the command as run, why it was run now, and the git analogue from the concept table below.
4. The first time a concept appears in the session, add the "where the analogue breaks" clause.
   After that, the git analogue alone is enough.
5. Close with the state after the turn: `@` (change ID, description, empty or not), the stack on trunk, and what is left for the human (approval, push, a decision).
6. Then write the normal turn summary.

Keep the section short enough to read in one screen.
The learner needs the flow and the commands, not a lecture.

## Concept table for git users

| jj concept                      | git analogue                                                                                       | Where the analogue breaks                                                                                                                                                        |
| ------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Working-copy commit `@`         | HEAD plus uncommitted changes, auto-amended                                                        | It is a real commit with its own ID. No dirty state, no staging area. git's HEAD points at `@-`.                                                                                 |
| Snapshot                        | `git add -A && git commit --amend --no-edit` before every jj command                               | Only when a jj command runs. Edits destroyed between two jj commands were never saved. Every unignored file is included.                                                         |
| No index                        | An empty `@` on top of a described change plays the index; `jj squash` is "commit the staged part" | Selection happens by path at squash time, not by staging earlier.                                                                                                                |
| Change ID vs commit ID          | Commit ID is the git SHA                                                                           | Change ID is a stable name for one piece of work that survives amend and rebase. Letters k to z, so it cannot be mistaken for hex.                                               |
| `jj describe`                   | `git commit --amend -m`, for any commit                                                            | Usually done before writing code.                                                                                                                                                |
| `jj new`                        | `git commit --allow-empty` and keep going                                                          | No branch is created or needed.                                                                                                                                                  |
| `jj commit -m`                  | `git commit -am`                                                                                   | Includes new files.                                                                                                                                                              |
| `jj squash`                     | `git commit --amend`                                                                               | Works between any two changes with `--from` and `--into`.                                                                                                                        |
| `jj split`                      | Undo the last commit and re-commit in two parts                                                    | Non-interactive only with paths and `-m`.                                                                                                                                        |
| `jj absorb`                     | `git absorb`                                                                                       | Built in. Rewrites several commits at once.                                                                                                                                      |
| Automatic rebase of descendants | `git rebase --update-refs` after every amend                                                       | Happens on every rewrite and never stops for conflicts.                                                                                                                          |
| Bookmark                        | Branch                                                                                             | Does not move when you commit. You move it, or push with `--named`. There is no current branch.                                                                                  |
| `name@origin`                   | `origin/name`                                                                                      | jj tracks ahead and behind, and turns a simultaneous move into a conflicted bookmark instead of an error.                                                                        |
| Push                            | `git push --force-with-lease`, always                                                              | There is no non-force mode. A rewritten bookmark is pushed as a force push with no flag.                                                                                         |
| Immutable commits               | "Do not rewrite published history" as a convention                                                 | Enforced, but by default only for trunk, tags, and untracked remote bookmarks. Pushed feature branches stay mutable unless configured.                                           |
| Conflict                        | Conflict markers during a rebase                                                                   | The rebase finishes. The conflict lives in the commit, marked `×` (or "(conflict)" on `@`). Fix it any time; descendants clear automatically. Default markers differ from git's. |
| Operation log                   | `git reflog` for the whole repo                                                                    | Undo replays repo state, including files on disk. It cannot undo a push.                                                                                                         |
| `jj undo`                       | `git reset --hard HEAD@{1}`                                                                        | Undoes the last operation, which may be a snapshot of edits the human just made.                                                                                                 |
| Workspace                       | `git worktree`                                                                                     | No branch-exclusivity rule. No `.git` inside. Can go stale.                                                                                                                      |
| Revset                          | `git log A..B`, `--author`, `--grep` in one language                                               | `::` is ancestry, `..` is range. String matching is a whole-string glob by default.                                                                                              |

## Narration shape

One line per command: "`<command>` — <why now>. git: <analogue>."
Add "; the jj difference: <break>" on first use of the concept in the session.
Example lines:

- `jj new -m "feat(auth): add token refresh"` — started the step as its own change so it can be kept or dropped on its own. git: `git switch -c` plus an empty commit; the jj difference: no branch name is needed and the parent's content stays in place.
- `jj squash --into kxrp -u src/auth.py` — the null check belongs to the change that introduced the function. git: `git add src/auth.py && git commit --fixup kxrp` then autosquash; the jj difference: no rebase step, descendants are rewritten automatically.
- `jj op log -n 5` — read before undo to confirm the top operation was mine. git: `git reflog`; the jj difference: the log covers the whole repo, and the top entry can be a snapshot of the human's unsaved edits.
