# Recovery

The op log is the undo history for the whole repo: commits, bookmarks, and the files on disk.
Read it before acting on it.

## Before any undo

1. `jj op log -n 5`.
   Each entry shows the operation ID, what it did, and the command that caused it.
2. Confirm the top entry is the agent's own operation.
   If it is a "snapshot working copy" entry that the agent did not cause, the human edited files since the last jj command.
   `jj undo` here undoes that snapshot and removes their files from disk.
3. Prefer `jj op revert <op>` with the exact operation ID over `jj undo`.
   It reverts that one operation and keeps later ones.
4. Never `jj undo` or `jj op restore` while another workspace is live.
   A jj issue reports that in 0.41 both rewind every workspace; not reproduced in the lab, treated as true.

## Undo the agent's last operation

- `jj op revert <op>` for one operation.
- `jj op restore <op>` to reset the whole repo to the state after `<op>`.
  It removes from disk any file snapshotted after that point.
  Note the current operation ID first so the reset can be reversed: `jj op log -n 1 --no-graph -T 'id.short(12)'`.
- After a revert, run `jj log` and look for `(divergent)` or a `/0`, `/1` suffix on a change ID.
  A later snapshot that rewrote the same change leaves two visible versions.
  Drop the unwanted copy by commit ID with `jj abandon <commit>`, and ask the human first if either copy holds their work.

## Recover a lost file

A file that disappeared after an undo or restore is still in the operation that snapshotted it.

1. Find that operation in `jj op log`.
2. `jj --at-op <op> log -r @ --no-graph -T commit_id` gives the commit that held the file.
3. `jj restore --from <commit> <path>` brings the file back into `@`.

## Conflicts

A rebase in jj always finishes.
A conflict is stored inside the commit and the files carry markers.
`jj log` marks a conflicted commit with `×`; the working copy keeps its `@` glyph and shows "(conflict)".

Before materializing a conflict (rebase, or new on a conflicted change), pass `--config ui.conflict-marker-style=git`.
The default style writes `%%%%%%%` diff sections that read nothing like git's markers.

Resolve in the working copy:

1. `jj log -r 'conflicts()'` to find the conflicted changes; `jj resolve --list -r <rev>` for the files.
2. Edit each file to its final content and remove every marker.
   The next jj command clears the conflict and rebases descendants, which clears theirs too.
3. To take one side whole: `jj resolve --tool :ours <path>` or `--tool :theirs <path>`.
   In a rebase, `:ours` is the destination and `:theirs` is the change being rebased.
4. For a conflict in an older change of the agent's own, detour and return.
   Record the stack top first: `top=$(jj log -r @ --no-graph -T change_id)`.
   Then `jj new <conflicted>`, which moves the working copy and changes the files on disk to that older state; fix the files; `jj squash -u`; then `jj new "$top"` to return to the top.
   Without the return step the next `jj new -m` builds a side branch off the older change.
   Descendants are rebased by the squash and their conflicts clear too.

The provenance rule decides what the agent resolves alone.
A resolution is justified when the descriptions of the changes on both sides, together with any spec or design document the repo keeps, say which content is intended.
When that trace exists, resolve and record it.
When it does not, stop and escalate.
A conflict against a change with no description has no provenance and is always escalated.

Report every conflict in the final message, resolved or not: the file, the description on each side, the resolution chosen, and the evidence it rested on.
An escalation shows the same minus the resolution, plus the question for the human.

## Divergent changes and conflicted bookmarks

- A change ID that resolves to several commits fails in revsets.
  Use commit IDs until the divergence is resolved.
- A bookmark shown as `name??` or "(conflicted)" after a fetch means both sides moved it.
  This is the human's decision: show `jj bookmark list <name>` and `jj log -r 'bookmarks(<name>) | remote_bookmarks(<name>)'` and stop.

## Stale workspace

"The working copy is stale" means another workspace rewrote this workspace's `@` or an ancestor.
Run `jj workspace update-stale`.
It moves the working copy to the recorded commit, so a file that existed only in the stale tree disappears from disk; recover it as above if needed.

## What recovery cannot do

- It cannot undo a push.
  If a secret or a bad commit reached the remote, tell the human; rewriting does not unpublish it.
- It cannot bring back edits that were never snapshotted.
  Files overwritten or deleted between two jj commands were never recorded.
