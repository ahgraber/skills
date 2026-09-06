# tmux, sockets, and sandbox settings

How the controller reaches target agents through tmux, what to do when a sandbox blocks it, and how to diagnose a window that will not take input.

- [Who starts the server](#who-starts-the-server) — and why it decides what the agents can do
- [Several controllers, one session](#several-controllers-one-session) — owners, and what `kill --all` reaches
- [How the session is laid out](#how-the-session-is-laid-out)
- [The socket](#the-socket)
- [When the sandbox blocks tmux](#when-the-sandbox-blocks-tmux) — the settings change, per platform
- [Sending text to a TUI](#sending-text-to-a-tui) — bracketed paste, submit keys
- [Reading idleness](#reading-idleness) — what `wait` can and cannot tell you
- [Troubleshooting](#troubleshooting)

## Who starts the server

tmux is a client/server program.
The server is a background daemon that forks every pane; a client such as `tmux new-window` only sends it a request.

**Each agent inherits the server's process environment, not the requesting client's.**
When the user starts the server, its agents run with the user's settings.
They are not subprocesses of the controller, and the controller's sandbox does not apply to them.
This is the reason to use tmux.

When the controller starts the server, its agents run inside the controller's sandbox.
That sandbox applies on top of the user's agent config, and nothing in the TUI reports it.
Seatbelt applies it on macOS; bubblewrap applies it on Linux and WSL2.
On macOS the failure is immediate: a sandbox that denies pty allocation lets the server start, then fails every window with `create window failed: fork failed`.

For this reason, `spawn` refuses to create a missing session unless a person runs the script with `--create-session` from their own terminal.

### The controller's sandbox does not reach the agents

The agent is forked by the user's server, a child of the user's shell rather than of the tool call that asked for the window.
The same probe script run in both places:

```text
                     controller   agent forked by the user's server
ps                   denied       ALLOWED
AF_UNIX bind         denied       ALLOWED
write outside allow  denied       ALLOWED
```

A controller that cannot write outside its allowlist can still start an agent that can.
This is intended, because an agent confined to the controller's policy could not do the work.
It also means the controller's sandbox does not limit what the agent does.
The agent CLI's own approval settings and the watching user are the only controls.

The session is the user's, not the script's, and can hold windows they opened.
Each window this script creates carries the tmux option `@agent-bridge`, so `kill --all` leaves the rest alone.

## Several controllers, one session

One session can host a controller per repository, all spawning into `agents`.
Without a record of who spawned what, one controller's `kill --all` would end another project's running work and report it as its own.

So each window carries `@agent-bridge-owner`: `AGENT_BRIDGE_OWNER` when it is set, else the git worktree root, else the working directory.
It stores a full path because two repositories can share a basename; `list` shows the basename.

| Command                      | Scope                                                     |
| ---------------------------- | --------------------------------------------------------- |
| `kill --all`                 | agents matching this owner                                |
| `send`, `keys`, named `kill` | refuse another owner's agents                             |
| `peek`, `wait`, `list`       | any window, since reading is what a shared session is for |

`--any-owner` lifts the restriction for one command, for when the user asks one controller to act on another's agent.

Windows with no owner recorded stay killable by anyone, so older agents do not become orphans.

The alternative is one session per project, `--session agents-<project>`.
Sessions on one server are already isolated, so this needs no owner logic; the user sees one project at a time and switches with `Ctrl-b s`.

## How the session is laid out

One session named `agents`, one window per agent, each running an agent CLI's TUI.
The window records which CLI it runs, so `send` uses that CLI's submit key.

Windows carry `remain-on-exit on`, so a crashed agent leaves a readable screen instead of vanishing.

A spawn does not switch the attached client to the new window — an agent that seized the terminal mid-keystroke would be worse than one the user navigates to.
`spawn` reports the index to press.

A session the user started is sized to their terminal, which is what `peek` captures.
`--create-session` makes a detached one at 200x50, because tmux would otherwise default to 80x24 and `peek` would return 80-column output.

## The socket

tmux puts its socket at `/tmp/tmux-$(id -u)/default` by default.
Both sides must use the same socket: the script that spawns agents and the human who attaches.

Keeping the default is what makes the human's command the plain one:

```bash
tmux attach -t agents
```

Two ways to point at a different socket, when the user runs their server on one:

- `--socket /path/to/socket` on any `agent_bridge.py` command.
- `AGENT_BRIDGE_SOCKET=/path/to/socket` in the environment.

Both change what the human types too — `agent_bridge.py attach` prints the matching command, so read it back rather than assuming.

Moving the socket is not a way around a sandbox.
The policy allowlists paths, so an unlisted destination is denied wherever it sits.
Fix the allowlist entry instead.

## When the sandbox blocks tmux

The script is not platform-specific; the sandbox around it is, and that decides which settings key to suggest.
Examples below use macOS paths — `/private/tmp` is the real path behind the `/tmp` symlink there, with no Linux equivalent.

| Error                                                       | Means                                               |
| ----------------------------------------------------------- | --------------------------------------------------- |
| `error connecting to .../default (Operation not permitted)` | the socket is blocked; this is the one that matters |
| `error creating .../default (Operation not permitted)`      | same block, hit while starting a server             |
| `directory .../tmux-501 has unsafe permissions`             | not a denial — tmux wants mode 0700; `chmod 700` it |

Even with the user owning the server, the controller still has to _connect_ to the socket, so an allowlist entry is needed either way.
One correct entry grants both connect and bind for that directory.

### Suggested settings change

Give this to the user; never edit their settings yourself.
The key differs by platform, and the macOS one is silently ignored elsewhere, so check the host first.

### macOS

```jsonc
{
  "sandbox": {
    "network": {
      // Directory paths, not globs, and narrower than "allowAllUnixSockets".
      "allowUnixSockets": ["/tmp/tmux-501", "/private/tmp/tmux-501"]
    }
  }
}
```

Replace `501` with the user's uid from `id -u`.

**No trailing `/*`.**
Entries compile to Seatbelt `(subpath ...)` rules — literal directory prefixes, not globs.
`"/tmp/tmux-501/*"` authorizes a directory named `*` and never matches `/tmp/tmux-501/default`.
This is the most common way the setting appears to do nothing: it loads, it shows up in the policy summary, and it grants a path that does not exist.

Both spellings are listed because `/tmp` is a symlink to `/private/tmp` and a rule against one may not cover the other.

### Linux and WSL2

Try tmux first — the block comes from a seccomp filter that may not be installed, and without it unix sockets are not blocked at all.
`/sandbox` reports this on its Dependencies tab.

If it is blocked, `allowUnixSockets` will not help: Claude Code's settings reference says it "ignores this list on Linux and WSL2, where the seccomp filter can't inspect socket paths".
The only key that works there is the blunt one:

```jsonc
{
  "sandbox": {
    "network": {
      "allowAllUnixSockets": true
    }
  }
}
```

Tell the user what it costs.
This is every unix socket, not tmux's — the same grant reaches `docker.sock` and any ssh-agent socket.
There is no path-scoped equivalent on Linux, so the choice is between no cross-harness control and a broad grant.

Adding `Bash(tmux:*)` to `permissions.allow` stops the per-command prompt, and is a separate decision.

### When the setting appears to do nothing

An entry can load and still match nothing; the policy summary proves only that it was read.
On Linux and WSL2 the key itself is ignored, so check the platform before the spelling.
On macOS, check for glob characters — to confirm rather than guess, bind a socket inside a directory named for the literal entry:

```python
import os, socket

os.mkdir("/private/tmp/tmux-501/*")  # a directory actually named '*'
socket.socket(socket.AF_UNIX, socket.SOCK_STREAM).bind("/private/tmp/tmux-501/*/probe.sock")
```

A bind that succeeds there while one beside the real socket fails proves the entry is a prefix pointing nowhere, and that dropping the `/*` is the fix.

Do not read a failed bind as AF_UNIX being blocked wholesale.
An allowlist matching nothing gives the same `EPERM` on every path, including one the process owns in a writable directory.

### If a glob-free entry still fails

The user runs the controller from their own terminal, where the script is unsandboxed and `--create-session` applies.
The scripted loop is off the table.

## Sending text to a TUI

`send` loads the message into a tmux buffer, pastes it with `paste-buffer -p`, then sends the submit key.

`-p` wraps the text in bracketed-paste markers.
Without it every newline arrives as a separate Enter, so the first line submits alone and the rest land as follow-ups.
This is the most common way scripted input to a TUI goes wrong.

Raise `--submit-delay` from 0.3s if a busy agent submits a partial message.

Use `keys` for anything that is not message text: `Escape` to interrupt, `C-c` to cancel, `Up` to recall the last message, `y` or `n` to answer an approval prompt.
Key names are tmux's, not Codex's.

## Reading idleness

`wait` hashes the captured screen on an interval and returns `idle` once the hash stops changing for `--settle` seconds.

This works because a working agent TUI repaints constantly — spinner, elapsed timer, streaming output.
It cannot tell apart the two reasons a screen holds still:

- the agent finished its turn and is waiting for input
- the agent is stopped on an approval prompt and is waiting for a human

Only the captured screen content distinguishes these states.

`wait` returns `dead` when the pane's process has exited, and `timeout` when `--timeout` elapses with the screen still moving.
A `timeout` is not a failure; it means the agent is still working.

## Troubleshooting

| Symptom                                          | Cause                                                                 | Fix                                                                    |
| ------------------------------------------------ | --------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `no tmux session named 'agents'`                 | the user has not started the server yet                               | ask them to run `tmux new-session -s agents`; do not start it yourself |
| `no agent named 'x'`                             | the window exited and was reaped, or the name is wrong                | `agent_bridge.py list`                                                 |
| spawn succeeds, window empty                     | the TUI has not drawn yet                                             | `peek` again after a second                                            |
| a `send` vanished                                | it landed before the composer existed                                 | prefer `--prompt` on spawn; otherwise `wait` before the first `send`   |
| message submitted in fragments                   | bracketed paste not reaching the TUI                                  | raise `--submit-delay`                                                 |
| an agent is denied a file the user can write     | the server was started from a sandbox and every agent inherited it    | the user restarts the session from their own terminal                  |
| `kill --all` left windows behind                 | they are the user's, or another project's agents                      | intended; `list` shows which, and `--any-owner` crosses the line       |
| `'x' was spawned for 'other'`                    | another controller sharing the session owns that agent                | leave it alone unless the user asks otherwise                          |
| `agent 'tests' already exists`                   | window names are one namespace across every controller                | name it for the work, such as `api-flaky-tests`                        |
| session missing after the user's terminal closed | the tmux server outlives clients, but not a reboot or a `kill-server` | the user starts it again                                               |
| the user sees no windows on attach               | they attached to a different socket                                   | use the command from `agent_bridge.py attach`                          |
