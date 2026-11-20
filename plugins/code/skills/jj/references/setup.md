# Setup checklist

For the human.
The agent verifies these at Orient with `scripts/jj_preflight.py` and, when one fails, walks you through the step here.
The agent does not run them.

## Once per machine

1. Install jj 0.41 or newer.
   `jj --version` prints the version.

2. Set your identity. jj does not read git's `user.name` and `user.email`; without them jj warns and creates commits that cannot be pushed.

   ```bash
   jj config set --user user.name "<your name>"
   jj config set --user user.email "<your email>"
   ```

3. Optional: give agents a signing key of their own, so agent-made changes are marked as such while the author stays you.
   The agent signs at Finalize with whatever mechanism your project instructions name.
   One way is a config file the agent passes with `--config-file`, which keeps the agent key out of your own config.
   The preflight checks `~/.config/jj/agent.toml`, or the path in `JJ_AGENT_CONFIG`, when that file exists.

   ```toml
   [signing]
   backend = "ssh"
   key = "/absolute/path/to/agent-signing-key"
   behavior = "own"
   ```

   A jj alias can wrap it, for example `aliases.agent-sign = ["--config-file", "<path>", "sign"]`.
   Then tell agents in your project instructions to sign with that alias.
   Without an agent key the agent leaves its changes unsigned and says so.

4. Make pushed history immutable. jj protects only trunk, tags, and untracked remote bookmarks by default; a pushed feature branch stays rewritable and is force-pushed without a flag.
   Add to your user config:

   ```toml
   [revset-aliases]
   "immutable_heads()" = "builtin_immutable_heads() | remote_bookmarks()"
   ```

   The preflight warns when this is absent.
   The agent's rewrite guard holds either way; the config turns a guard into a refusal.

5. Git-style conflict markers, so an agent reads conflicts the way it reads git's:

   ```toml
   [ui]
   conflict-marker-style = "git"
   ```

6. Optional, recommended for agents: `ui.paginate = "never"` and `ui.color = "never"` in the same file, so no jj command waits on a pager.

`jj config set --user` writes these; `jj config path --user` shows the file.

## Once per repo

1. Check `.gitignore` first.
   `jj git init --colocate` snapshots every unignored file into `@` at init, not at the first later command, so build output, secrets, and scratch files must be ignored before you run it.
   If you keep agent workspaces inside the repo under `.worktrees/`, ignore that directory too.

2. An existing git clone becomes colocated with one command at the repo root.

   ```bash
   jj git init --colocate
   ```

   It is non-destructive: git keeps working and every change you had, staged or not, is kept.
   Your in-flight edits land in one undescribed `@`, so the agent's first preflight will stop with `decision-required` and ask you how to close them.
   Git's HEAD stays on your branch until a later jj command rewrites `@-`; from then on `git status` shows `HEAD (no branch)`.
   A new repo: `jj git init` is colocated by default in 0.41.

3. Verify: `jj git colocation status`, then `jj st`.

4. Teach mode for this repo, if you want it on every session: add a line that reads exactly `jj: teach` to the repo's `AGENTS.md`, `CLAUDE.md`, or `CLAUDE.local.md`.

## What changes for your git habits

- Commit with jj or with git in a given session, not both.
  A `git commit` is imported by jj on its next command, with any unstaged edits left in a new `@`.
  Legal, but it muddles the history the learner is reading.
- Git hooks do not run under jj.
  The agent runs the hook runner itself at Finalize; when you commit with git directly, hooks run as before.
- `git status` in a colocated repo shows `HEAD (no branch)` and the contents of `@` as unstaged.
  That is normal.
- Secondary jj workspaces have no `.git`.
  Git tooling runs from the default workspace.
