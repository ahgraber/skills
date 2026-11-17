# Finalize

The one approval gate of the turn.
Nothing in it is optional.
The agent never pushes.

## Steps

1. Snapshot: `jj st`.
   Read it.
   Every unignored file in the tree is now part of `@`; a scratch file or a secret here goes into the change.

2. Guard the stack: `jj log -r '<base>..@ & ::remote_bookmarks()' --no-graph -T 'change_id.short() ++ "\n"'` must print nothing.
   `<base>` is the change the preflight reported at Orient; `<base>..@` is exactly the agent's changes from this turn.
   If the guard prints a change, that change was pushed; do not reword, squash into, or rebase it.
   Anything that must change on it becomes a new change on top.

3. Run the repo's hooks yourself. jj runs no git hooks: `jj commit`, `jj describe`, and `jj git push` all skip pre-commit, commit-msg, and pre-push, and push goes out with `--no-verify`.
   Run it before step 8, while `@` is the top of the stack.

   When jj-hooks is available (an alias from Orient wraps `jj-hooks run`, or `jj-hooks` is on PATH), check the stack as one diff between exact commit IDs:

   ```bash
   from=$(jj log -r '<base>' --no-graph -T commit_id)
   to=$(jj log -r '@' --no-graph -T commit_id)
   JJ_HOOKS_NO_DIRENV_ALLOW=1 jj-hooks run --stage pre-commit --from "$from" --to "$to" --result-json "$TMPDIR/jj-hooks-result.json"
   ```

   Through an alias that wraps `jj-hooks run`, append the same `--from`, `--to`, and `--result-json` arguments to the alias.
   Always pass `--from` and `--to`.
   Given a revset that contains `@` instead (jj-hooks' default, and what a bare alias passes), a hook that rewrites a file leaves a bookmark that jj 0.41 cannot forget, and the next jj command abandons the whole stack, the human's changes included.
   That failure was reproduced by replaying jj-hooks 0.7.0's command sequence, not by running jj-hooks; recover with `references/recovery.md`, restoring to the operation before "import git refs".
   Read the result file, not the exit code, which is 0 both when hooks pass and when the repo has none.
   `phase` `runner-completed` with `exit` 0 is a pass; `no-config` means the repo has no hooks; `fixup` means a hook rewrote files; anything else is a failure.
   On `fixup`, jj-hooks has added a new change on top of `@` holding the edits.
   Route them with `jj absorb --from <fixup> --into '<base>..@'`, then run the hooks again.
   If edits remain in the fixup, report them at the step 5 stop and abandon the fixup only on approval.
   In a sandbox that blocks `~/.local/state`, also set `JJ_HOOKS_WORKTREE_ROOT` and `XDG_STATE_HOME` to directories under `$TMPDIR`.
   This form follows jj-hooks 0.7.0's CLI definitions and has not been run.

   Without jj-hooks, use the repo's hook runner on the changed files.
   In the default colocated workspace, git sees every jj change as a commit with HEAD at `@-` and the edits in `@` as unstaged, so a git-based file list works when its base is the branch base rather than HEAD:

   ```bash
   { git diff -z --name-only --diff-filter=d "$(git merge-base HEAD main)"; git ls-files -z --others --exclude-standard; } | xargs -0 prek run --files
   ```

   Replace `prek` with the repo's runner and `main` with its trunk.
   The untracked-file half of the list covers the whole checkout, so an in-repo `.worktrees/` directory must be git-ignored or other agents' files reach the hook run; the preflight warns when it is not.
   In a secondary jj workspace there is no `.git`; jj-hooks handles that itself, and without it use the temp-worktree detour in `references/workspaces.md`.
   Fix every failure before going on.

4. Confirm no conflicts: `jj log -r 'conflicts() & <base>..@'` must print nothing.
   Push refuses a conflicted or undescribed commit, so the human would hit it later otherwise.

5. Present the stack.
   Show `jj log -r '<base>..@' --no-graph -T 'change_id.short() ++ "  " ++ description.first_line() ++ "\n"'` and `jj diff --stat --from '<base>' --to @`.
   When the preflight reported no trunk bookmark, say so; `trunk()` then resolves to the root commit and is not a useful base for anything.
   State the proposed final description for each change.
   If a `commit-message` skill is available in the harness, draft the descriptions with it; otherwise follow the repo's convention.
   Offer, in one line, to squash the stack coarser (to one change, or named pairs).
   Then stop and wait for approval.
   In teach mode this stop carries the plan block.

6. On approval: apply the final descriptions with `jj describe -r <rev> -m "<text>"` for each change that needs one, and any squash the human chose with `jj squash --from <rev> --into <rev> -u`.
   For a multi-line message use `printf '%s\n' "<subject>" "" "<body>" | jj describe -r <rev> --stdin`.

7. Sign the agent's changes with the agent signing key, when one is configured.
   Use the mechanism the project instructions or the user's setup name: a jj alias, a config file passed with `--config-file`, or per-command `--config signing.*` values.
   With no agent key configured, skip this step and report that the agent's changes are unsigned.
   Whatever the mechanism, select the changes with `-r '<base>..@ & ~empty()'` and never run `jj sign` without `-r`.
   Without `-r`, `jj sign` signs every mutable change reachable from `@`, including the human's.
   The range is positional, not by author, because the agent and the human share one email: a revset such as `mine()` would select the human's unpushed changes beneath the stack.
   `jj sign` rewrites what it selects, so the range must hold nothing but the agent's own changes.
   The author stays the human; the agent key marks the changes as agent-made.

8. Leave `@` empty on top of the stack: if `@` holds content, `jj new` after signing so the next snapshot does not rewrite a signed change.

9. Hand over.
   The final message lists the changes with their change IDs and, in teach mode, the jj section.
   Name the stack top by change ID; `@-` is the top only right after step 8 ran.

Do not re-run steps 1 to 4 from memory.
Run them again if any edit happened after they ran.

## What the human does to push

The agent does not run these.
In teach mode, include the applicable ones in the final message so the learner sees the handoff.

- New branch: `jj git push --named <name>=<top change ID> --dry-run`, read the verbs, then the same without `--dry-run`. "add" and "move forward" are safe. "move sideways" or "move backward" means a force push.
- Existing branch: `jj bookmark move <name> --to <top change ID>`, then `jj git push --bookmark <name> --dry-run`, then push.
- Pull request from a colocated repo: `gh pr create --head <name>` from the default workspace, because git's HEAD is detached.
  Not verified on 0.41, so treat it as the expected form.
- A later squash by the human replaces the agent-signed commits with new ones.
  Those are signed only if the human's own jj config signs; otherwise they are unsigned, the same as a `git commit --amend` without `-S`.
