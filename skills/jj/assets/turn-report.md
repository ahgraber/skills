# Turn report template (teach mode)

Place this section in the final message of the turn, before the normal turn summary.
Fill it from `scripts/jj_turn_log.py --since <op>`; group by the phases that ran; one line per command.
Add the "jj difference" clause only on the first use of a concept in the session.

```md
### jj this turn

**Start**
- `jj new -m "<intent>"` — <why now>. git: <analogue>; the jj difference: <break>.

**Work**
- `jj st` is omitted; it only records edits.
- `jj new -m "<next intent>"` — <why now>. git: <analogue>.
- `jj squash --into <rev> -u <paths>` — <why now>. git: <analogue>.

**Finalize**
- `prek run --files ...` — jj runs no git hooks, so the checks ran by hand.
- `jj describe -r <rev> -m "<final text>"` — <why now>. git: <analogue>.
- `jj --config-file <agent.toml> sign -r '<base>..@ & ~empty()'` — <why now>. git: <analogue>.

**Recover** (only if it ran)
- `jj op log -n 5` — <why now>. git: <analogue>.
- `jj op revert <op>` — <why now>. git: <analogue>.

**Conflicts** (only if any)
- `<file>`: ours "<description>" vs theirs "<description>". Resolved: <what>. Evidence: <descriptions or spec>. | Escalated: <question>.

**State after this turn**
- `@`: <change id> "<description>" (empty | <n> files)
- Stack on trunk: <change id> "<description>"; <change id> "<description>"
- For you: <approve the stack | push with `jj git push --named <name>=<top change ID> --dry-run` | a decision>
```

A plan block at a confirmation stop uses the same line shape for the step not yet run:

```md
### jj next
- `jj rebase -s <rev> -o 'trunk()'` — <why>. git: <analogue>. Waiting for your go.
```
