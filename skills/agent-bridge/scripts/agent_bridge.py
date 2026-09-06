#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = []
# ///
"""Bridge to coding-agent TUIs through windows of one tmux session.

Each target agent is one CLI's terminal UI in its own tmux window. A controlling process uses
`spawn`, `send`, `keys`, `peek`, `wait`, `list`, and `kill` to work with those agents while a human
watches them in the same session. Per-CLI differences live in `ADAPTERS`.

Run `agent_bridge.py --help` for the command list.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import sys
import time

SESSION = "agents"
"""Default tmux session name."""

WINDOW_WIDTH = 200
WINDOW_HEIGHT = 50
"""Geometry for a detached session, which tmux would otherwise create at 80x24, truncating `peek`."""

WINDOW_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
"""Window names are used as tmux targets and must not contain `:` or `.`-leading forms."""

PROMPT_UNSUPPORTED = "unsupported"
"""`prompt_flag` value for a CLI with no established initial-prompt form; those adapters refuse `--prompt`."""


@dataclass(frozen=True)
class Adapter:
    """What one coding-agent CLI needs that the others do not."""

    name: str
    binary: str
    dangerous_flags: frozenset[str] = frozenset()
    """Flags that remove the human approval gate. Refused without an explicit opt-in."""
    dangerous_values: dict[str, frozenset[str]] = field(default_factory=dict)
    """Flag/value pairs that remove the gate, for CLIs that spell it as a mode rather than a switch."""
    config_assignment_flags: frozenset[str] = frozenset()
    """Flags taking `key=value` that override config, such as Codex's `-c`."""
    dangerous_config_keys: dict[str, frozenset[str]] = field(default_factory=dict)
    """Config keys, and the values for them, that remove the gate when set through `config_assignment_flags`."""
    opaque_config_flags: frozenset[str] = frozenset()
    """Flags that select config this script does not inspect, such as a named profile or settings file.

    Not refused; the spawn reports the posture as `OVERRIDDEN`.
    """
    prompt_flag: str | None = PROMPT_UNSUPPORTED
    """How an initial prompt is passed: `None` for positional, a flag string, or `PROMPT_UNSUPPORTED`."""
    model_flag: str | None = None
    submit_key: str = "Enter"
    """tmux key name that submits a composed message."""
    config_hint: str = ""
    """Where this CLI keeps its own approval configuration, for the spawn's posture report."""


ADAPTERS: dict[str, Adapter] = {
    "codex": Adapter(
        name="codex",
        binary="codex",
        dangerous_flags=frozenset(
            {
                "--dangerously-bypass-approvals-and-sandbox",
                "--dangerously-bypass-hook-trust",
                "--full-auto",
                "--yolo",
            }
        ),
        dangerous_values={
            "--sandbox": frozenset({"danger-full-access"}),
            "-s": frozenset({"danger-full-access"}),
            "--ask-for-approval": frozenset({"never"}),
            "-a": frozenset({"never"}),
        },
        config_assignment_flags=frozenset({"-c", "--config"}),
        dangerous_config_keys={
            "approval_policy": frozenset({"never"}),
            "sandbox_mode": frozenset({"danger-full-access"}),
        },
        opaque_config_flags=frozenset({"-p", "--profile"}),
        prompt_flag=None,
        model_flag="--model",
        config_hint="~/.codex/config.toml",
    ),
    "claude": Adapter(
        name="claude",
        binary="claude",
        dangerous_flags=frozenset({"--dangerously-skip-permissions", "--allow-dangerously-skip-permissions"}),
        dangerous_values={"--permission-mode": frozenset({"bypassPermissions", "dontAsk"})},
        opaque_config_flags=frozenset({"--settings", "--setting-sources"}),
        prompt_flag=None,
        model_flag="--model",
        config_hint="~/.claude/settings.json",
    ),
    "copilot": Adapter(
        name="copilot",
        binary="copilot",
        dangerous_flags=frozenset({"--allow-all-tools", "--allow-all", "--yolo"}),
        model_flag="--model",
        config_hint="~/.copilot (COPILOT_HOME)",
    ),
    "gemini": Adapter(
        name="gemini",
        binary="gemini",
        dangerous_flags=frozenset({"--yolo", "-y"}),
        dangerous_values={"--approval-mode": frozenset({"yolo"})},
        model_flag="--model",
        config_hint="~/.gemini/settings.json",
    ),
    "cursor": Adapter(
        name="cursor",
        binary="cursor-agent",
        dangerous_flags=frozenset({"--force", "-f"}),
        model_flag="--model",
    ),
    "pi": Adapter(
        name="pi",
        binary="pi",
        config_hint="~/.pi",
    ),
}
"""The target agent CLIs this controller knows how to launch.

An adapter left at `PROMPT_UNSUPPORTED` spawns bare and takes its first instruction through `send`.
"""

DEFAULT_ADAPTER = "codex"

MANAGED_OPTION = "@agent-bridge"
"""tmux user option set on every window this script creates, holding the adapter name.

A window without it is one the user opened; `send`, `keys`, and `kill` refuse those.
"""

OWNER_OPTION = "@agent-bridge-owner"
"""tmux user option holding which project a window's agent was spawned for.

The value is a full path, so two repositories sharing a basename stay distinct; `list` shows the
basename.
"""

FATAL_TMUX_ERRORS = (
    "operation not permitted",
    "permission denied",
    "error creating",
    "couldn't create directory",
)
"""tmux failures that mean the socket is unreachable, not that the session is absent."""

NO_SERVER_ERRORS = (
    "no server running",
    "no such file or directory",
)
"""tmux failures that mean no server is listening on the socket."""


class BridgeError(Exception):
    """A controller operation failed with a message meant to be shown to the caller."""


def default_owner() -> str:
    """Return the project this invocation is working in.

    The git worktree root, else the working directory. `AGENT_BRIDGE_OWNER` overrides both.
    """
    override = os.environ.get("AGENT_BRIDGE_OWNER")
    if override:
        return override
    proc = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0 and proc.stdout.strip():
        return proc.stdout.strip()
    return str(Path.cwd().resolve())


def owner_label(owner: str) -> str:
    """Return an owner path's basename for display, or the path itself when it has none."""
    return Path(owner).name or owner


def positive_seconds(text: str) -> float:
    """Parse a finite duration above zero, raising `argparse.ArgumentTypeError` otherwise."""
    value = float(text)
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError(f"expected a positive number of seconds, got {text!r}")
    return value


def non_negative_seconds(text: str) -> float:
    """Parse a finite duration at or above zero, raising `argparse.ArgumentTypeError` otherwise."""
    value = float(text)
    if not math.isfinite(value) or value < 0:
        raise argparse.ArgumentTypeError(f"expected zero or more seconds, got {text!r}")
    return value


def non_negative_lines(text: str) -> int:
    """Parse a line count at or above zero, raising `argparse.ArgumentTypeError` otherwise."""
    value = int(text)
    if value < 0:
        raise argparse.ArgumentTypeError(f"expected zero or more lines, got {text!r}")
    return value


@dataclass
class Tmux:
    """A tmux client bound to one socket and one session."""

    session: str = SESSION
    socket: str | None = None
    owner: str = field(default_factory=default_owner)
    """The project this controller acts for; scopes `send`, `keys`, and `kill` to its own agents."""

    def _base(self) -> list[str]:
        cmd = ["tmux"]
        if self.socket:
            cmd += ["-S", self.socket]
        return cmd

    def _exec(self, args: tuple[str, ...], stdin: str | None) -> subprocess.CompletedProcess[str]:
        """Run one tmux command.

        `TMUX` is cleared so it targets the configured server, not a session this process runs under.
        """
        env = dict(os.environ)
        env.pop("TMUX", None)
        return subprocess.run(  # noqa: S603
            [*self._base(), *args],
            input=stdin,
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def run(self, *args: str, stdin: str | None = None) -> str:
        """Run one tmux command and return its stdout, raising `BridgeError` on failure."""
        proc = self._exec(args, stdin)
        if proc.returncode != 0:
            detail = (proc.stderr or proc.stdout).strip()
            raise BridgeError(f"tmux {' '.join(args)}: {detail or f'exit {proc.returncode}'}")
        return proc.stdout

    def server_running(self) -> bool:
        """Report whether any tmux server is listening on the socket.

        Raises `BridgeError` when the socket itself is unreachable, which is not the same as no
        server.
        """
        proc = self._exec(("has-session", "-t", f"={self.session}"), None)
        if proc.returncode == 0:
            return True
        stderr = (proc.stderr or "").strip()
        lowered = stderr.lower()
        if any(marker in lowered for marker in FATAL_TMUX_ERRORS):
            raise BridgeError(
                f"cannot reach tmux: {stderr}\n"
                "The sandbox is refusing the socket. If an allowlist entry is already in place, "
                "check it for a trailing '/*': these entries are literal path prefixes, not "
                "globs, so a glob authorizes a directory that does not exist. See "
                "references/tmux-and-sandbox.md, and give the user the corrected setting as a "
                "suggestion."
            )
        return not any(marker in lowered for marker in NO_SERVER_ERRORS)

    def session_exists(self) -> bool:
        """Report whether the configured session is running.

        Raises `BridgeError` when the tmux socket is unreachable, rather than reporting no agents.
        """
        proc = self._exec(("has-session", "-t", f"={self.session}"), None)
        if proc.returncode == 0:
            return True
        stderr = (proc.stderr or "").strip()
        if any(marker in stderr.lower() for marker in FATAL_TMUX_ERRORS):
            raise BridgeError(
                f"cannot reach tmux: {stderr}\n"
                "The sandbox is refusing the socket. If an allowlist entry is already in place, "
                "check it for a trailing '/*': these entries are literal path prefixes, not "
                "globs, so a glob authorizes a directory that does not exist. See "
                "references/tmux-and-sandbox.md, and give the user the corrected setting as a "
                "suggestion."
            )
        return False

    def windows(self) -> list[dict[str, str]]:
        """List the session's windows, newest last.

        `cli` names the adapter for windows this script spawned and is empty for the user's own.
        """
        if not self.session_exists():
            return []
        fmt = (
            f"#{{window_id}}\t#{{window_name}}\t#{{pane_pid}}\t#{{pane_dead}}"
            f"\t#{{{MANAGED_OPTION}}}\t#{{{OWNER_OPTION}}}"
        )
        out = self.run("list-windows", "-t", f"={self.session}", "-F", fmt)
        rows: list[dict[str, str]] = []
        for line in out.splitlines():
            if not line.strip():
                continue
            wid, name, pid, dead, cli, owner = line.split("\t")
            rows.append(
                {
                    "id": wid,
                    "name": name,
                    "pid": pid,
                    "state": "dead" if dead == "1" else "running",
                    "cli": cli,
                    "owner": owner,
                }
            )
        return rows

    def server_env(self, name: str) -> str | None:
        """Return one variable from the tmux server's global environment, or None when unset.

        The server forks every agent, so this is the environment agents inherit, not this
        process's.
        """
        try:
            out = self.run("show-environment", "-g", name)
        except BridgeError:
            return None
        prefix = f"{name}="
        for line in out.splitlines():
            if line.startswith(prefix):
                return line[len(prefix) :]
        return None

    def adapter_for(self, name: str) -> Adapter | None:
        """Return the adapter recorded on a window, or None when this script did not spawn it."""
        for win in self.windows():
            if win["name"] == name:
                return ADAPTERS.get(win["cli"])
        return None

    def window_id(self, name: str, *, managed_only: bool = True, any_owner: bool = False) -> str:
        """Resolve an exact window name to its stable `@id`.

        Raises `BridgeError` when no window matches, when the window was not spawned by this
        script, or when it was spawned for another project. Read-only callers pass
        `managed_only=False`; `any_owner=True` skips the ownership check.
        """
        windows = self.windows()
        for win in windows:
            if win["name"] != name:
                continue
            if managed_only and not win["cli"]:
                raise BridgeError(
                    f"{name!r} is a window this script did not spawn, so it belongs to the "
                    "user. Refusing to send input to it or kill it: a paste and Enter in "
                    "the user's shell runs as a command. Act on it in your own terminal."
                )
            if managed_only and not any_owner and win["owner"] and win["owner"] != self.owner:
                raise BridgeError(
                    f"{name!r} was spawned for {owner_label(win['owner'])!r}, not "
                    f"{owner_label(self.owner)!r}. Another controller is driving it and is not "
                    "expecting anyone else to. Pass --any-owner only if the user asks you to "
                    "act on another project's agent."
                )
            return win["id"]
        known = ", ".join(w["name"] for w in windows) or "none"
        raise BridgeError(f"no agent named {name!r} in session {self.session!r} (running: {known})")


@dataclass
class Posture:
    """Which approval settings a spawned agent will run under."""

    source: str = ""
    default_config: bool = True
    """False when an argument points the CLI at configuration other than its default."""
    notes: list[str] = field(default_factory=list)


def binary_on_server_path(tmux: Tmux, binary: str) -> bool:
    """Report whether the tmux server would find `binary`.

    Falls back to this process's `PATH` when the server's cannot be read.
    """
    path = tmux.server_env("PATH")
    return shutil.which(binary, path=path) is not None


def find_dangerous(adapter: Adapter, passthrough: list[str]) -> list[str]:
    """Return the passthrough arguments that would disable this CLI's approval gate.

    Covers three shapes: a named switch, a flag whose value names a mode, and a config
    assignment that reaches the same setting the switch would.
    """
    found = []
    for i, arg in enumerate(passthrough):
        if arg in adapter.dangerous_flags:
            found.append(arg)
            continue

        flag, _, inline = arg.partition("=")
        following = passthrough[i + 1] if i + 1 < len(passthrough) else ""

        values = adapter.dangerous_values.get(flag)
        if values:
            if (inline or following) in values:
                found.append(f"{flag} {inline or following}".strip())
            continue

        if flag in adapter.config_assignment_flags:
            assignment = inline or following
            key, _, value = assignment.partition("=")
            if value in adapter.dangerous_config_keys.get(key.strip(), frozenset()):
                found.append(f"{flag} {assignment}")
    return found


def find_opaque_config(adapter: Adapter, passthrough: list[str]) -> list[str]:
    """Return passthrough arguments that load config this script cannot inspect."""
    return [arg for arg in passthrough if arg.partition("=")[0] in adapter.opaque_config_flags]


def resolve_posture(adapter: Adapter, passthrough: list[str], *, accept_risk: bool) -> Posture:
    """Report the approval posture a spawn will run under.

    A spawn adds no approval or sandbox flags; the agent runs on its own configuration. Raises
    `BridgeError` when `passthrough` would remove the human approval gate and `accept_risk` is
    false.
    """
    dangerous = find_dangerous(adapter, passthrough)
    if dangerous and not accept_risk:
        joined = ", ".join(dangerous)
        raise BridgeError(
            f"refusing to spawn {adapter.name} with {joined}: an agent that never asks for "
            "approval is not overseen by the human watching the window. Pass "
            "--i-accept-unattended-risk to override."
        )

    posture = Posture()
    if dangerous:
        posture.source = "caller override"
        posture.notes.append(f"unattended spawn accepted: {', '.join(dangerous)}")
        return posture

    hint = f" ({adapter.config_hint})" if adapter.config_hint else ""
    posture.source = f"{adapter.name} defaults"
    posture.notes.append(f"no flags added; {adapter.name} runs on its own configuration{hint}")

    overrides = find_opaque_config(adapter, passthrough)
    if overrides:
        posture.default_config = False
        posture.notes.append(
            f"not the default configuration: {', '.join(overrides)} selects config this script "
            "does not read, so the approval settings in force are whatever it contains"
        )
    return posture


def cmd_spawn(tmux: Tmux, args: argparse.Namespace) -> dict:
    """Create a tmux window running one coding-agent CLI."""
    if not WINDOW_NAME_RE.match(args.name):
        raise BridgeError(f"invalid agent name {args.name!r}: use letters, digits, dot, dash, underscore")
    if any(w["name"] == args.name for w in tmux.windows()):
        raise BridgeError(f"agent {args.name!r} already exists; kill it first or pick another name")

    adapter = ADAPTERS.get(args.agent)
    if adapter is None:
        known = ", ".join(sorted(ADAPTERS))
        raise BridgeError(f"unknown agent {args.agent!r}; known adapters: {known}")
    if not binary_on_server_path(tmux, adapter.binary):
        raise BridgeError(f"{adapter.binary} is not on the tmux server's PATH")

    posture = resolve_posture(adapter, args.agent_args, accept_risk=args.i_accept_unattended_risk)

    agent_cmd = [adapter.binary]
    if args.model:
        if adapter.model_flag is None:
            raise BridgeError(f"--model is not wired up for {adapter.name}; pass it after -- instead")
        agent_cmd += [adapter.model_flag, args.model]
    agent_cmd += args.agent_args
    if args.prompt:
        if adapter.prompt_flag == PROMPT_UNSUPPORTED:
            raise BridgeError(
                f"{adapter.name} has no established interactive initial-prompt flag here, and "
                "guessing one risks a headless run that exits. Spawn without --prompt, then "
                f'`wait {args.name}` and `send {args.name} "..."`.'
            )
        if adapter.prompt_flag:
            agent_cmd.append(adapter.prompt_flag)
        agent_cmd.append(args.prompt)

    shell_cmd = shlex.join(agent_cmd)

    workdir = None
    if args.cd:
        resolved = Path(args.cd).expanduser().resolve()
        if not resolved.is_dir():
            raise BridgeError(f"--cd {args.cd}: not a directory")
        workdir = str(resolved)

    # `remain-on-exit` must be set before the agent runs: a CLI that exits immediately is
    # reaped, and its final screen with it, before the option lands.
    created_session = False
    if tmux.session_exists():
        window_cmd = ["new-window", "-d", "-P", "-F", "#{window_id}", "-t", f"={tmux.session}:", "-n", args.name]
        if workdir:
            window_cmd += ["-c", workdir]
        window = tmux.run(*window_cmd).strip()
    elif args.create_session:
        session_cmd = [
            "new-session",
            "-d",
            "-P",
            "-F",
            "#{window_id}",
            "-s",
            tmux.session,
            "-n",
            args.name,
            "-x",
            str(WINDOW_WIDTH),
            "-y",
            str(WINDOW_HEIGHT),
        ]
        if workdir:
            session_cmd += ["-c", workdir]
        window = tmux.run(*session_cmd).strip()
        created_session = True
    else:
        raise BridgeError(
            f"no tmux session named {tmux.session!r}. Ask the user to start it in their own "
            f"terminal:\n\n    tmux new-session -s {tmux.session}\n\n"
            "tmux forks every agent from the server process, so a session started from here "
            "would hand this process's sandbox to each agent. Pass --create-session only when "
            "this script is being run from the user's own terminal."
        )

    tmux.run("set-option", "-w", "-t", window, "remain-on-exit", "on")
    tmux.run("set-option", "-w", "-t", window, MANAGED_OPTION, adapter.name)
    tmux.run("set-option", "-w", "-t", window, OWNER_OPTION, tmux.owner)
    tmux.run("respawn-pane", "-k", "-t", window, shell_cmd)

    return {
        "agent": args.name,
        "cli": adapter.name,
        "owner": tmux.owner,
        "window": window,
        "session": tmux.session,
        "created_session": created_session,
        "command": shell_cmd,
        "watch": watch_command(tmux, window),
        "posture": {
            "source": posture.source,
            "default_config": posture.default_config,
            "config": adapter.config_hint,
            "notes": posture.notes,
        },
        "attach": attach_command(tmux),
    }


def cmd_send(tmux: Tmux, args: argparse.Namespace) -> dict:
    """Paste a message into an agent's composer and submit it."""
    window = tmux.window_id(args.name, any_owner=args.any_owner)
    text = read_message(args)
    if not text.strip():
        raise BridgeError("refusing to send an empty message")

    adapter = tmux.adapter_for(args.name)
    submit_key = args.submit_key or (adapter.submit_key if adapter else "Enter")

    buffer_name = f"agent-bridge-{os.getpid()}"
    tmux.run("load-buffer", "-b", buffer_name, "-", stdin=text)

    # `-p` wraps the text in bracketed-paste markers, so the TUI takes a multi-line message as
    # one paste. Without it every newline reaches the composer as Enter and submits a fragment.
    tmux.run("paste-buffer", "-d", "-p", "-b", buffer_name, "-t", window)

    submitted = not args.no_submit
    if submitted:
        time.sleep(args.submit_delay)
        tmux.run("send-keys", "-t", window, submit_key)

    return {
        "agent": args.name,
        "cli": adapter.name if adapter else "",
        "window": window,
        "bytes": len(text.encode()),
        "submitted": submitted,
        "submit_key": submit_key if submitted else "",
    }


def read_message(args: argparse.Namespace) -> str:
    """Return the message text from `--file`, positional text, or stdin, in that order."""
    if args.file:
        if args.file == "-":
            return sys.stdin.read()
        return Path(args.file).expanduser().read_text()
    if args.text:
        return " ".join(args.text)
    if not sys.stdin.isatty():
        return sys.stdin.read()
    raise BridgeError("no message: pass text, --file PATH, or pipe it on stdin")


def cmd_keys(tmux: Tmux, args: argparse.Namespace) -> dict:
    """Send raw tmux key names for TUI control that is not a message: `Escape`, `C-c`, `Up`, `y`."""
    window = tmux.window_id(args.name, any_owner=args.any_owner)
    tmux.run("send-keys", "-t", window, *args.keys)
    return {"agent": args.name, "window": window, "keys": args.keys}


def capture(tmux: Tmux, window: str, history: int = 0) -> str:
    """Capture an agent's visible screen, optionally with scrollback."""
    cmd = ["capture-pane", "-p", "-t", window]
    if history:
        cmd += ["-S", f"-{history}"]
    return tmux.run(*cmd)


def cmd_peek(tmux: Tmux, args: argparse.Namespace) -> dict:
    """Return what an agent's window currently shows.

    Captures only, so it is allowed on any window, including ones this script did not spawn.
    """
    window = tmux.window_id(args.name, managed_only=False)
    text = capture(tmux, window, args.history).rstrip("\n")
    lines = text.splitlines()
    if args.lines:
        lines = lines[-args.lines :]
    return {"agent": args.name, "window": window, "screen": "\n".join(lines)}


def cmd_wait(tmux: Tmux, args: argparse.Namespace) -> dict:
    """Block until an agent's screen stops changing for `--settle` seconds.

    An idle result means the agent is waiting, either finished or stopped on an approval prompt;
    use `peek` to tell those apart. Captures only, so it runs against any window.
    """
    window = tmux.window_id(args.name, managed_only=False)
    deadline = time.monotonic() + args.timeout
    last_digest = None
    stable_since = None

    while time.monotonic() < deadline:
        if any(w["id"] == window and w["state"] == "dead" for w in tmux.windows()):
            return {"agent": args.name, "window": window, "status": "dead"}
        digest = hashlib.sha256(capture(tmux, window).encode()).hexdigest()
        now = time.monotonic()
        if digest != last_digest:
            last_digest = digest
            stable_since = now
        elif stable_since is not None and now - stable_since >= args.settle:
            return {
                "agent": args.name,
                "window": window,
                "status": "idle",
                "settled_for": round(now - stable_since, 1),
            }
        time.sleep(args.poll)

    return {"agent": args.name, "window": window, "status": "timeout", "timeout": args.timeout}


def cmd_list(tmux: Tmux, _args: argparse.Namespace) -> dict:
    """List every target agent in the session.

    `status` is one of "no-server", "no-session", or "running"; `agents` is populated only for
    the last.
    """
    if not tmux.server_running():
        status = "no-server"
    elif not tmux.session_exists():
        status = "no-session"
    else:
        status = "running"
    agents = tmux.windows() if status == "running" else []
    return {
        "session": tmux.session,
        "status": status,
        "owner": tmux.owner,
        "agents": agents,
        "attach": attach_command(tmux),
    }


def cmd_kill(tmux: Tmux, args: argparse.Namespace) -> dict:
    """Kill named agents, or with `--all` every agent this controller spawned.

    `--all` keeps the user's own windows and other projects' agents, and lists them under "kept".
    """
    if args.all:
        if not tmux.session_exists():
            return {"killed": [], "kept": [], "session": tmux.session, "note": "session was not running"}
        windows = tmux.windows()
        killed, kept = [], []
        for win in windows:
            mine = win["cli"] and (args.any_owner or not win["owner"] or win["owner"] == tmux.owner)
            if mine:
                tmux.run("kill-window", "-t", win["id"])
                killed.append(win["name"])
            else:
                kept.append(win["name"])
        return {"killed": killed, "kept": kept, "session": tmux.session, "owner": tmux.owner}
    if not args.name:
        raise BridgeError("name an agent to kill, or pass --all")
    killed = []
    for name in args.name:
        tmux.run("kill-window", "-t", tmux.window_id(name, any_owner=args.any_owner))
        killed.append(name)
    return {"killed": killed, "kept": [], "session": tmux.session, "owner": tmux.owner}


def attach_command(tmux: Tmux) -> str:
    """Return the command a human runs to watch the target agents."""
    socket = f"-S {shlex.quote(tmux.socket)} " if tmux.socket else ""
    return f"tmux {socket}attach -t {shlex.quote(tmux.session)}"


def watch_command(tmux: Tmux, window: str) -> str:
    """Return the attach command plus the key that switches to this agent's window."""
    try:
        index = tmux.run("display-message", "-p", "-t", window, "#{window_index}").strip()
    except BridgeError:
        index = ""
    key = f"Ctrl-b {index}" if index else "Ctrl-b w"
    return f"{attach_command(tmux)}, then {key}"


def cmd_attach(tmux: Tmux, _args: argparse.Namespace) -> dict:
    """Return the human's attach command; this script never attaches.

    `running` is None with a `note` when the socket cannot be reached, since the human's
    terminal is not under this process's sandbox.
    """
    result: dict = {"session": tmux.session, "attach": attach_command(tmux)}
    try:
        result["running"] = tmux.session_exists()
    except BridgeError as exc:
        result["running"] = None
        result["note"] = str(exc)
    return result


ANY_OWNER_HELP = "act on agents spawned for another project; only when the user asks for it"


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="agent-bridge",
        description="Drive coding-agent CLIs as windows of one tmux session.",
    )
    parser.add_argument("--session", default=SESSION, help=f"tmux session name (default: {SESSION})")
    parser.add_argument(
        "--socket",
        default=os.environ.get("AGENT_BRIDGE_SOCKET"),
        help="tmux socket path; also read from AGENT_BRIDGE_SOCKET. Use when the user's server "
        "runs on a non-default socket.",
    )
    parser.add_argument(
        "--owner",
        default=os.environ.get("AGENT_BRIDGE_OWNER"),
        help="project these agents belong to; defaults to the git repository root, else the "
        "working directory. Also read from AGENT_BRIDGE_OWNER.",
    )
    parser.add_argument("--json", action="store_true", help="emit JSON instead of text")

    # `SUPPRESS` keeps an absent subcommand flag from resetting the value the top-level parser
    # already resolved.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--session", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--socket", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--owner", default=argparse.SUPPRESS, help=argparse.SUPPRESS)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="emit JSON instead of text")

    sub = parser.add_subparsers(dest="command", required=True, parser_class=argparse.ArgumentParser)

    spawn = sub.add_parser(
        "spawn",
        parents=[common],
        help="start an agent CLI in a new window",
        epilog="Put extra CLI flags after --, for example: spawn api --cd ~/src -- --search",
    )
    spawn.add_argument("name", help="agent name; becomes the tmux window name")
    spawn.add_argument(
        "--agent",
        default=DEFAULT_ADAPTER,
        choices=sorted(ADAPTERS),
        help=f"which agent CLI to run (default: {DEFAULT_ADAPTER})",
    )
    spawn.add_argument("--cd", help="working directory for the agent's window")
    spawn.add_argument("--model", help="model for this agent")
    spawn.add_argument("--prompt", help="initial prompt; starts the agent working immediately")
    spawn.add_argument(
        "--i-accept-unattended-risk",
        action="store_true",
        help="allow flags that disable the agent's approval gate",
    )
    spawn.add_argument(
        "--create-session",
        action="store_true",
        help="create the tmux session when it is missing; only correct when this script is run "
        "from the user's own terminal, since every agent inherits the server's sandbox",
    )
    spawn.add_argument(
        "agent_args",
        nargs="*",
        metavar="-- AGENT_ARG",
        help="extra arguments passed through to the agent CLI; must follow a -- separator",
    )
    spawn.set_defaults(func=cmd_spawn)

    send = sub.add_parser("send", parents=[common], help="paste a message into an agent and submit it")
    send.add_argument("name")
    send.add_argument("text", nargs="*", help="message text; omit to read stdin")
    send.add_argument("--file", help="read the message from a file, or - for stdin")
    send.add_argument("--no-submit", action="store_true", help="paste without submitting")
    send.add_argument(
        "--submit-delay", type=non_negative_seconds, default=0.3, help="seconds between paste and submit"
    )
    send.add_argument(
        "--submit-key",
        help="tmux key name that submits; defaults to the key recorded for the window's CLI",
    )
    send.add_argument("--any-owner", action="store_true", help=ANY_OWNER_HELP)
    send.set_defaults(func=cmd_send)

    keys = sub.add_parser("keys", parents=[common], help="send raw tmux key names (Escape, C-c, Up, y)")
    keys.add_argument("name")
    keys.add_argument("keys", nargs="+")
    keys.add_argument("--any-owner", action="store_true", help=ANY_OWNER_HELP)
    keys.set_defaults(func=cmd_keys)

    peek = sub.add_parser("peek", parents=[common], help="show an agent's current screen")
    peek.add_argument("name")
    peek.add_argument("-n", "--lines", type=non_negative_lines, default=0, help="show only the last N lines")
    peek.add_argument("--history", type=non_negative_lines, default=0, help="include N lines of scrollback")
    peek.set_defaults(func=cmd_peek)

    wait = sub.add_parser("wait", parents=[common], help="block until an agent's screen stops changing")
    wait.add_argument("name")
    wait.add_argument(
        "--settle", type=non_negative_seconds, default=5.0, help="seconds of no change that count as idle"
    )
    wait.add_argument("--timeout", type=positive_seconds, default=600.0, help="give up after this many seconds")
    wait.add_argument("--poll", type=positive_seconds, default=1.0, help="seconds between screen captures")
    wait.set_defaults(func=cmd_wait)

    listing = sub.add_parser("list", parents=[common], help="list target agents")
    listing.set_defaults(func=cmd_list)

    kill = sub.add_parser("kill", parents=[common], help="kill agents or the whole session")
    kill.add_argument("name", nargs="*")
    kill.add_argument("--all", action="store_true", help="kill every agent this controller spawned")
    kill.add_argument("--any-owner", action="store_true", help=ANY_OWNER_HELP)
    kill.set_defaults(func=cmd_kill)

    attach = sub.add_parser("attach", parents=[common], help="print the command a human runs to watch target agents")
    attach.set_defaults(func=cmd_attach)

    return parser


def render(result: dict, command: str) -> str:
    """Render a result as text for a human or a controlling agent to read."""
    if command == "peek":
        return result["screen"]
    if command == "list":
        session = result["session"]
        if result["status"] == "no-server":
            return (
                f"no tmux server is running. Ask the user to start the session in their own "
                f"terminal:\n\n    tmux new-session -s {session}"
            )
        if result["status"] == "no-session":
            return f"a tmux server is running, but it has no session named {session!r}"
        agents = result["agents"]
        if not agents:
            return f"session {session!r} has no windows"
        rows = []
        for a in agents:
            kind = a["cli"] or "user window"
            foreign = f"  [{owner_label(a['owner'])}]" if a["owner"] and a["owner"] != result["owner"] else ""
            rows.append(f"{a['name']}\t{a['state']}\tpid {a['pid']}\t{a['id']}\t{kind}{foreign}")
        footer = [f"owner: {owner_label(result['owner'])}", f"watch: {result['attach']}"]
        return "\n".join([*rows, "", *footer])
    if command == "spawn":
        posture = result["posture"]
        source = posture["source"] if posture["default_config"] else f"{posture['source']} (OVERRIDDEN)"
        lines = [
            f"spawned {result['agent']} ({result['cli']}, {result['window']}) in session {result['session']}",
            f"  command: {result['command']}",
            f"  posture: {source}",
        ]
        lines += [f"  {note}" for note in posture["notes"]]
        lines.append(f"  watch: {result['watch']}")
        return "\n".join(lines)
    return json.dumps(result, indent=2)


def main(argv: list[str] | None = None) -> int:
    """Parse arguments, run the command, print the result."""
    parser = build_parser()
    args = parser.parse_args(argv)
    tmux = Tmux(session=args.session, socket=args.socket, owner=args.owner or default_owner())

    if shutil.which("tmux") is None:
        print("error: tmux is not on PATH", file=sys.stderr)
        return 2

    try:
        result = args.func(tmux, args)
    except BridgeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result, indent=2) if args.json else render(result, args.command))
    return 0


if __name__ == "__main__":
    sys.exit(main())
