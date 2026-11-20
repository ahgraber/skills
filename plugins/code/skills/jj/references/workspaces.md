# Parallel agents with jj workspaces

A jj workspace is a second working copy of the same repo, with its own `@`, sharing the commits and the op log.
One workspace per agent keeps the human's working copy untouched, because the agent's files are in a separate directory.

## The constraint on 0.41

A secondary workspace has `.jj` but no `.git`.
Inside it, `git status` and the hook runners `prek` and `pre-commit` fail with "not a git repository" (verified on 0.41); `gh` needs a git checkout too and is expected to fail the same way (not verified).
A harness git worktree has the opposite problem: `.git` but no `.jj`, so jj commands fail there.
The two cannot be combined on 0.41.
`jj workspace add --colocate` exists only in unreleased jj; check `jj workspace add --help` for it and prefer it when present.

So a parallel agent in a jj workspace has jj, and reaches git tooling only through the detour below.

## Create

Run from the default workspace, one workspace at a time; a jj issue reports that concurrent `jj workspace add` calls can break the calling workspace (not reproduced).

```bash
jj workspace add --name <agent> -r 'trunk()' <path>
```

The path is either outside the repo (for example `~/_code/_worktrees/<repo>/<branch>`) or inside a `.worktrees/` directory that `.gitignore` excludes.
An in-repo directory that git does not ignore puts the other agents' files into every `git ls-files --others` run, which is what the Finalize hook step uses; the preflight warns when `.worktrees/` exists and is not ignored.
The parent directory must exist before `jj workspace add` runs; it does not create it.
The workspace's `@` is visible from every workspace as `<agent>@`.
The author of every change stays the human in parallel mode too; agents are told apart by workspace name, not by author.

## Rules while several workspaces are live

- No `jj undo` and no `jj op restore` in any workspace.
  A jj issue reports that both rewind every workspace in 0.41; not reproduced, treated as true.
  Use `jj op revert <op>` for one operation.
- Never rewrite another workspace's `@` or its ancestors.
  Doing so makes that workspace stale and it refuses commands until `jj workspace update-stale` runs there, which can remove files from its disk.
- Each agent follows the normal loop inside its own workspace.
  The rewrite guard and the never-do list apply unchanged.

## Hooks from a workspace: the temp-worktree detour

When jj-hooks is available, use the jj-hooks command in `references/finalize.md` step 3 instead; it finds the primary `.git` from a workspace and builds its own temporary worktree.
This detour is the fallback without it.

The hook runner needs a git checkout of exactly the commit under test.
Build one from the default workspace, run the hooks there, and remove it.
Verified: the default workspace's git index and HEAD are unchanged afterward.

```bash
# in the agent workspace: snapshot, then read the commit
jj st
commit=$(jj log -r @ --no-graph -T commit_id)

# from the default workspace
git worktree add --detach "$TMPDIR/hooks-<agent>" "$commit"
( cd "$TMPDIR/hooks-<agent>" && prek run --files <changed files> )
git worktree remove --force "$TMPDIR/hooks-<agent>"
git worktree prune
```

Get the changed files from `jj diff --name-only -r @` in the agent workspace.
A hook that rewrites files (a formatter) changes the temporary worktree, not the jj change; copy those edits back into the workspace and snapshot, or run the formatter first through `jj fix` when the repo configures `fix.tools`.
Use a fresh temp directory per run and always prune.

Rejected alternatives: pointing the hook runner at the main repo with `GIT_DIR` rewrites the human's git index; checking the agent's commit out in the default workspace replaces the human's files.

## Merge and clean up

- Combine results with `jj new <a>@ <b>@ -m "<text>"` or by rebasing one stack onto the other, then review the merge like any other change.
- A PR from a workspace: the bookmark can be pushed from any workspace by the human; `gh pr create --head <name>` runs from the default workspace (not verified on 0.41).
- Remove a finished workspace with `jj workspace forget <agent>` and then delete its directory.
  `forget` leaves the files and keeps the commit.
