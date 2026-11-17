# jj commands for agents

Verified against jj 0.41.0 unless a row says "not verified".
Every command takes `--no-pager --color=never`; the tables omit them.
`<rev>` accepts a change ID, a commit ID, a bookmark, or a revset.

Flags that keep an agent safe:

- `-m "<text>"` on `new`, `describe`, `commit`, `split`, and `squash` when both sides have a description.
  Without it jj opens an editor.
  `JJ_EDITOR=false` in the environment turns that hang into an error.
- `-u` on `squash` keeps the destination's message.
- `--git` on `diff` and `show` gives a git patch instead of the default word-colored diff.
- `--no-graph -T '<template>'` on `log` and `op log` gives parseable output.
- `--config ui.conflict-marker-style=git` on `rebase` and `new` writes git-style conflict markers.
- `<base>` in a revset below is the change the preflight reported at Orient; `<base>..@` is the agent's own changes and nothing else.

## Orient

| Intent                     | Command                                                                                               | git analogue                     | For the learner                                                                         |
| -------------------------- | ----------------------------------------------------------------------------------------------------- | -------------------------------- | --------------------------------------------------------------------------------------- |
| Is this a jj repo          | `jj root`                                                                                             | `git rev-parse --show-toplevel`  | Fails outside a jj repo. `.jj` next to `.git` means colocated.                          |
| Colocation                 | `jj git colocation status`                                                                            | none                             | Says whether git commands also work here.                                               |
| What changed, where am I   | `jj st`                                                                                               | `git status`                     | Shows `@` and its parent `@-`. Running it snapshots the files into `@`.                 |
| Recent history             | `jj log`                                                                                              | `git log --graph`                | Shows mutable work plus trunk. `@` marks the working copy, `◆` marks immutable commits. |
| Parseable history          | `jj log -r 'trunk()..@' --no-graph -T 'change_id.short() ++ " " ++ description.first_line() ++ "\n"'` | `git log --format=...`           | Templates replace format strings.                                                       |
| Diff of current work       | `jj diff --git`                                                                                       | `git diff HEAD`                  | No staging area, so this is everything in `@`.                                          |
| Diff of one change         | `jj show --git <rev>`                                                                                 | `git show <rev>`                 |                                                                                         |
| Changed file names         | `jj diff --name-only -r <rev>`                                                                        | `git diff --name-only`           | No NUL option; pipe through `tr '\n' '\0'` for `xargs -0`.                              |
| Is a change on a remote    | `jj log -r '<rev> & ::remote_bookmarks()'`                                                            | `git branch -r --contains`       | Non-empty means a rewrite would force-push.                                             |
| File at a revision         | `jj file show -r <rev> <path>`                                                                        | `git show <rev>:<path>`          | `jj cat` was removed.                                                                   |
| Undo history               | `jj op log -n 5`                                                                                      | `git reflog`, for the whole repo | Every jj command is an operation.                                                       |
| Bookmarks and remote state | `jj bookmark list --all`                                                                              | `git branch -vv -a`              | `*` after a name means local and remote differ.                                         |
| Workspaces                 | `jj workspace list`                                                                                   | `git worktree list`              |                                                                                         |
| Look without snapshotting  | `jj --ignore-working-copy log`                                                                        | none                             | Use when the human's half-finished edits must not be recorded yet.                      |

Revsets that matter: `@`, `@-`, `trunk()`, `trunk()..@`, `::@`, `mutable()`, `mine()`, `conflicts()`, `remote_bookmarks()`, `bookmarks(<name>)`, `description(substring:"<text>")`, `subject("<text>")`, `<workspace>@`.
String patterns are whole-string globs by default; a description ends in a newline, so `description("feat: x")` matches nothing.
Use `substring:` or `subject()`.

## Start

| Intent                     | Command                             | git analogue                    | For the learner                                                   |
| -------------------------- | ----------------------------------- | ------------------------------- | ----------------------------------------------------------------- |
| Name the intent first      | `jj describe -m "<text>"`           | `git commit --amend -m` on HEAD | Describing before coding is normal. The text can change any time. |
| New change on top of `@`   | `jj new -m "<text>"`                | none; git would commit first    | The old `@` becomes `@-` and keeps its content.                   |
| New change on trunk        | `jj new trunk() -m "<text>"`        | `git switch -c x origin/main`   | No branch name needed.                                            |
| Insert a change before `@` | `jj new -B @ -m "<text>" --no-edit` | interactive rebase              | `-A` inserts after. Descendants rebase automatically.             |

## Work

| Intent                                               | Command                                            | git analogue                                 | For the learner                                                                                                             |
| ---------------------------------------------------- | -------------------------------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Record edits                                         | any jj command                                     | `git add -A && git commit --amend --no-edit` | There is no `add`. Every untracked, unignored file is included.                                                             |
| Finish this change, start the next                   | `jj commit -m "<text>"`                            | `git commit -am`                             | Same as `describe -m` then `new`.                                                                                           |
| Reword any change                                    | `jj describe -r <rev> -m "<text>"`                 | `rebase -i` reword                           | Descendants rebase automatically. Refused on immutable commits.                                                             |
| Fold `@` into its parent                             | `jj squash -u`                                     | `git commit --amend`                         | `-u` keeps the parent's message.                                                                                            |
| Fold some files into the parent                      | `jj squash -u <paths>`                             | `git add <paths> && git commit --amend`      | The rest stays in `@`.                                                                                                      |
| Move content between changes                         | `jj squash --from <rev> --into <rev> -u <paths>`   | fixup via `rebase -i`                        | `jj move` was removed.                                                                                                      |
| Route fixes to the changes that introduced the lines | `jj absorb --into '<base>..@'`                     | `git absorb` (third party)                   | Rewrites several changes. Read the list it prints. Without `--into` it targets every mutable change, including the human's. |
| Stop tracking a file                                 | add to `.gitignore`, then `jj file untrack <path>` | `git rm --cached`                            | Refuses unless the file is ignored.                                                                                         |
| Force a snapshot                                     | `jj st`                                            | none                                         | Files are recorded only when a jj command runs.                                                                             |

## Organize

| Intent                          | Command                        | git analogue                           | For the learner                                                    |
| ------------------------------- | ------------------------------ | -------------------------------------- | ------------------------------------------------------------------ |
| Split `@` by path               | `jj split -m "<text>" <paths>` | `reset HEAD~`, `add <paths>`, `commit` | Listed paths go to the first change. Without paths it opens a TUI. |
| Rebase a change and descendants | `jj rebase -s <rev> -o <dest>` | `git rebase --onto`                    | Never stops halfway. Conflicts are stored in the commits.          |
| Rebase one change               | `jj rebase -r <rev> -o <dest>` | drop plus cherry-pick                  | Its children move onto its old parent.                             |
| Rebase the stack onto trunk     | `jj rebase -b @ -o trunk()`    | `git rebase main`                      | Not verified on 0.41; the help text documents it.                  |
| Drop a change                   | `jj abandon <rev>`             | `rebase -i` drop                       | Deletes its bookmarks locally. Recoverable with `jj undo`.         |
| How a change evolved            | `jj evolog -r <rev>`           | none                                   | Every snapshot and rewrite of one change ID.                       |
| Revert a commit                 | `jj revert -r <rev> -B @`      | `git revert`                           | `jj backout` was removed.                                          |

## Share

The agent does not push.
These rows explain what the human runs.

| Intent                               | Command                                                          | git analogue                              | For the learner                                                                                                                          |
| ------------------------------------ | ---------------------------------------------------------------- | ----------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Fetch                                | `jj git fetch`                                                   | `git fetch`                               | Never touches the working copy.                                                                                                          |
| Create a bookmark                    | `jj bookmark create <name> -r <rev>`                             | `git branch <name> <rev>`                 | Bookmarks do not follow new commits.                                                                                                     |
| Move a bookmark forward              | `jj bookmark move <name> --to <rev>`                             | `git branch -f`, forward only             | Refuses backward or sideways without `--allow-backwards`.                                                                                |
| Preview a push                       | `jj git push --named <name>=<rev> --dry-run`                     | `git push --dry-run`                      | Read the verb: "add" and "move forward" are safe; "move sideways" or "move backward" is a force push.                                    |
| Push under a chosen name             | `jj git push --named <name>=<rev>`                               | `git push origin <rev>:refs/heads/<name>` | The one-shot form for a PR branch.                                                                                                       |
| Push a change under a generated name | `jj git push --change <rev>`                                     | push to `push-<id>`                       | Creates and tracks `push-<changeid>`.                                                                                                    |
| Push an existing bookmark            | `jj git push --bookmark <name>`                                  | `git push origin <name>`                  | Behaves like `--force-with-lease` every time.                                                                                            |
| Sign the agent's changes             | `jj --config-file <agent config> sign -r '<base>..@ & ~empty()'` | `git commit --amend -S`                   | Rewrites the selected commits, so run before the first push. Positional range, never `mine()`: the agent and the human share one author. |

## Recover

| Intent                         | Command                                       | git analogue                           | For the learner                                                                    |
| ------------------------------ | --------------------------------------------- | -------------------------------------- | ---------------------------------------------------------------------------------- |
| Undo the last operation        | `jj undo`                                     | `git reset --hard HEAD@{1}`            | Read `jj op log` first. The last operation may be a snapshot of the human's edits. |
| Revert one operation           | `jj op revert <op>`                           | none                                   | Applies the inverse of that operation and keeps later ones.                        |
| Reset to an earlier operation  | `jj op restore <op>`                          | none                                   | Resets commits, bookmarks, and files on disk.                                      |
| Look at an earlier state       | `jj --at-op <op> log`                         | none                                   | Read-only time travel.                                                             |
| Recover a file from a snapshot | `jj restore --from <commit> <path>`           | `git checkout <rev> -- <path>`         | Get the commit from `jj --at-op <op> log -r @ --no-graph -T commit_id`.            |
| Find conflicted changes        | `jj log -r 'conflicts()'`                     | `git status` mid-rebase                |                                                                                    |
| List conflicted files          | `jj resolve --list -r <rev>`                  | `git diff --name-only --diff-filter=U` | Without `--list` it launches a merge tool.                                         |
| Take one side                  | `jj resolve --tool :ours <path>` or `:theirs` | `git checkout --ours`                  | In a rebase, `:ours` is the destination, `:theirs` the rebased change.             |
| Fix a stale workspace          | `jj workspace update-stale`                   | none                                   | Needed after another workspace rewrote this one's `@`.                             |

## Parallel

| Intent                     | Command                                                 | git analogue          | For the learner                                                                |
| -------------------------- | ------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------ |
| New workspace for an agent | `jj workspace add --name <name> -r <rev> <path>`        | `git worktree add`    | Shares the repo and op log. Its `@` is visible as `<name>@`. No `.git` inside. |
| Remove a workspace         | `jj workspace forget <name>`, then delete the directory | `git worktree remove` | `forget` leaves the files and the commit.                                      |

## Renamed and removed

| Old                              | Now                                                   | Removed in         |
| -------------------------------- | ----------------------------------------------------- | ------------------ |
| `jj branch`                      | `jj bookmark`                                         | 0.30               |
| `jj checkout`                    | `jj new` or `jj edit`                                 | 0.24               |
| `jj merge a b`                   | `jj new a b`                                          | 0.24               |
| `jj move`                        | `jj squash --from --into`                             | 0.24               |
| `jj unsquash`                    | `jj squash --from @- --into @`                        | 0.28               |
| `jj untrack`                     | `jj file untrack`                                     | 0.28               |
| `jj cat`, `jj files`, `jj chmod` | `jj file show`, `jj file list`, `jj file chmod`       | 0.26               |
| `jj backout`                     | `jj revert`                                           | 0.35               |
| `jj op undo <op>`                | `jj op revert <op>`                                   | 0.39               |
| `jj undo <op>`                   | `jj op revert <op>`                                   | rejected in 0.41   |
| `jj obslog`                      | `jj evolog`                                           | still accepted     |
| `jj split --siblings`            | `jj split --parallel`                                 | 0.26               |
| `-l N` on log                    | `-n N`                                                | 0.26               |
| `jj git push --allow-new`        | not needed; `-b`, `-c`, `--named` track automatically | deprecated in 0.36 |
| `jj rebase -d`                   | `-o` / `--onto`                                       | still accepted     |
| `branches()` revset              | `bookmarks()`                                         | 0.28               |

Not in 0.41: `jj workspace add --colocate`, `jj workspace remove`, `jj undo --allow-cross-workspace`, `jj converge`.
