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
   Use the repo's hook runner on the changed files.
   In the default colocated workspace, git sees every jj change as a commit with HEAD at `@-` and the edits in `@` as unstaged, so a git-based file list works when its base is the branch base rather than HEAD:

   ```bash
   { git diff -z --name-only --diff-filter=d "$(git merge-base HEAD main)"; git ls-files -z --others --exclude-standard; } | xargs -0 prek run --files
   ```

   Replace `prek` with the repo's runner and `main` with its trunk.
   The untracked-file half of the list covers the whole checkout, so an in-repo `.worktrees/` directory must be git-ignored or other agents' files reach the hook run; the preflight warns when it is not.
   In a secondary jj workspace there is no `.git`; use the temp-worktree detour in `references/workspaces.md`.
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

7. Sign the agent's changes with the agent config: `jj --config-file <agent.toml> sign -r '<base>..@ & ~empty()'`.
   The author stays the human; the agent key signs.
   The range is positional, not by author, because the agent and the human share one email: a revset such as `mine()` would select the human's unpushed changes beneath the stack and rewrite them.
   `jj sign` rewrites what it selects, so the range must hold nothing but the agent's own changes.
   The agent config path comes from the preflight output.

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
