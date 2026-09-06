#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8.0",
# ]
# ///
"""Tests for the agent-bridge `agent_bridge.py` script.

These cover the parts that decide behavior without a live tmux server: the adapter registry,
the safety posture resolver, the dangerous-flag detector, name validation, message resolution,
and argument parsing. The tmux integration itself is exercised by `agent_bridge.py list`
against a real server, which needs a socket and so does not run here.
"""

from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "agent-bridge" / "scripts" / "agent_bridge.py"

SOCKET = "/private/tmp/agent-bridge/socket"
"""A socket path standing in for one the caller overrode."""

_spec = importlib.util.spec_from_file_location("bridge", SCRIPT)
assert _spec is not None
assert _spec.loader is not None
bridge = importlib.util.module_from_spec(_spec)
# `@dataclass` resolves annotations through `sys.modules[cls.__module__]`, so the module has to
# be registered before it executes.
sys.modules["bridge"] = bridge
_spec.loader.exec_module(bridge)


# --- dangerous flag detection ------------------------------------------------


@pytest.mark.parametrize(
    "passthrough",
    [
        ["--dangerously-bypass-approvals-and-sandbox"],
        ["--dangerously-bypass-hook-trust"],
        ["--full-auto"],
        ["--yolo"],
        ["-a", "never"],
        ["--ask-for-approval", "never"],
        ["--ask-for-approval=never"],
        ["-s", "danger-full-access"],
        ["--sandbox=danger-full-access"],
        ["--model", "gpt-5.6-sol", "-s", "danger-full-access"],
    ],
)
def test_find_dangerous_flags(passthrough):
    assert bridge.find_dangerous(CODEX, passthrough)


@pytest.mark.parametrize(
    "passthrough",
    [
        [],
        ["--model", "gpt-5.6-sol"],
        ["-s", "workspace-write"],
        ["--sandbox=read-only"],
        ["-a", "on-request"],
        # A value that merely contains the word must not trip the check.
        ["--model", "never-mind"],
    ],
)
def test_safe_flags_are_not_flagged(passthrough):
    assert bridge.find_dangerous(CODEX, passthrough) == []


# --- per-adapter gate detection ----------------------------------------------


@pytest.mark.parametrize(
    ("agent", "passthrough"),
    [
        ("claude", ["--dangerously-skip-permissions"]),
        ("claude", ["--permission-mode", "bypassPermissions"]),
        ("claude", ["--permission-mode=dontAsk"]),
        ("copilot", ["--allow-all-tools"]),
        ("copilot", ["--yolo"]),
        ("gemini", ["-y"]),
        ("gemini", ["--approval-mode=yolo"]),
        ("cursor", ["--force"]),
    ],
)
def test_each_adapter_detects_its_own_gate_removal(agent, passthrough):
    assert bridge.find_dangerous(bridge.ADAPTERS[agent], passthrough)


@pytest.mark.parametrize(
    ("agent", "passthrough"),
    [
        # A gate-removing flag for one CLI is not one for another.
        ("claude", ["--dangerously-bypass-approvals-and-sandbox"]),
        ("codex", ["--dangerously-skip-permissions"]),
        ("claude", ["--permission-mode", "acceptEdits"]),
        ("gemini", ["--approval-mode=default"]),
    ],
)
def test_gate_detection_does_not_leak_between_adapters(agent, passthrough):
    assert bridge.find_dangerous(bridge.ADAPTERS[agent], passthrough) == []


@pytest.mark.parametrize(
    "passthrough",
    [
        ["-c", "approval_policy=never"],
        ["-c=approval_policy=never"],
        ["--config", "approval_policy=never"],
        ["-c", "sandbox_mode=danger-full-access"],
        ["--model", "gpt-5.6-sol", "-c", "approval_policy=never"],
    ],
)
def test_config_assignment_reaching_the_gate_is_refused(passthrough):
    """A general config override reaches the same setting the named switch would."""
    assert bridge.find_dangerous(bridge.ADAPTERS["codex"], passthrough)


@pytest.mark.parametrize(
    "passthrough",
    [
        ["-c", "approval_policy=on-request"],
        ["-c", "model=gpt-5.6-sol"],
        ["-c", "sandbox_mode=workspace-write"],
    ],
)
def test_harmless_config_assignments_pass(passthrough):
    assert bridge.find_dangerous(bridge.ADAPTERS["codex"], passthrough) == []


@pytest.mark.parametrize(
    ("agent", "passthrough"),
    [
        ("codex", ["--profile", "something"]),
        ("codex", ["-p", "something"]),
        ("claude", ["--settings", "other-settings.json"]),
    ],
)
def test_config_selecting_flags_are_reported(agent, passthrough):
    """A profile or settings file replaces the CLI's default config; the spawn says so."""
    posture = bridge.resolve_posture(bridge.ADAPTERS[agent], passthrough, accept_risk=False)
    assert posture.default_config is False
    assert any("not the default configuration" in note for note in posture.notes)


def test_a_plain_spawn_uses_the_default_config():
    posture = bridge.resolve_posture(bridge.ADAPTERS["claude"], [], accept_risk=False)
    assert posture.default_config is True


def test_every_adapter_names_a_binary():
    for name, adapter in bridge.ADAPTERS.items():
        assert adapter.binary, name
        assert adapter.name == name


def test_default_adapter_is_registered():
    assert bridge.DEFAULT_ADAPTER in bridge.ADAPTERS


# --- posture resolution ------------------------------------------------------

CODEX = bridge.ADAPTERS["codex"]


def test_dangerous_spawn_is_refused_by_default():
    with pytest.raises(bridge.BridgeError, match="refusing to spawn"):
        bridge.resolve_posture(CODEX, ["--dangerously-bypass-approvals-and-sandbox"], accept_risk=False)


def test_refusal_names_the_agent():
    with pytest.raises(bridge.BridgeError, match="claude"):
        bridge.resolve_posture(bridge.ADAPTERS["claude"], ["--dangerously-skip-permissions"], accept_risk=False)


def test_dangerous_spawn_allowed_with_explicit_opt_in():
    posture = bridge.resolve_posture(CODEX, ["--dangerously-bypass-approvals-and-sandbox"], accept_risk=True)
    assert posture.source == "caller override"


def test_every_adapter_runs_on_its_own_configuration():
    """A spawn adds no approval flags: injecting one would override the user's own setup."""
    for name in bridge.ADAPTERS:
        posture = bridge.resolve_posture(bridge.ADAPTERS[name], [], accept_risk=False)
        assert posture.source == f"{name} defaults", name
        assert posture.default_config is True, name


def test_the_posture_names_where_the_configuration_lives():
    posture = bridge.resolve_posture(CODEX, [], accept_risk=False)
    assert "~/.codex/config.toml" in posture.notes[0]


def test_no_sandbox_or_approval_flags_reach_the_command(monkeypatch):
    """The spawned command carries only the binary and what the caller passed."""
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    result = bridge.cmd_spawn(tmux, spawn_args())
    assert result["command"] == "codex"


# --- window names ------------------------------------------------------------


@pytest.mark.parametrize("name", ["api", "api-tests", "worker_1", "a.b", "A1"])
def test_valid_window_names(name):
    assert bridge.WINDOW_NAME_RE.match(name)


@pytest.mark.parametrize("name", ["", "-lead", ".hidden", "a:b", "a b", "a/b", "a$b"])
def test_invalid_window_names(name):
    assert not bridge.WINDOW_NAME_RE.match(name)


# --- message resolution ------------------------------------------------------


def ns(**kwargs) -> argparse.Namespace:
    """Build a namespace with the fields `read_message` reads."""
    return argparse.Namespace(**{"file": None, "text": [], **kwargs})


def test_message_from_positional_text():
    assert bridge.read_message(ns(text=["run", "the", "tests"])) == "run the tests"


def test_message_from_file(tmp_path):
    path = tmp_path / "brief.md"
    path.write_text("line one\nline two\n")
    assert bridge.read_message(ns(file=str(path))) == "line one\nline two\n"


def test_message_from_stdin(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _FakeStdin("piped brief"))
    assert bridge.read_message(ns()) == "piped brief"


def test_missing_message_is_an_error(monkeypatch):
    monkeypatch.setattr(sys, "stdin", _FakeStdin("", tty=True))
    with pytest.raises(bridge.BridgeError, match="no message"):
        bridge.read_message(ns())


class _FakeStdin:
    """Minimal stdin stand-in for `read_message`."""

    def __init__(self, data: str, tty: bool = False):
        self._data = data
        self._tty = tty

    def read(self) -> str:
        return self._data

    def isatty(self) -> bool:
        return self._tty


# --- reachability ------------------------------------------------------------


def fake_exec(returncode: int, stderr: str = ""):
    """Return a `Tmux._exec` stand-in with a fixed result."""

    def _exec(_args, _stdin):
        return subprocess.CompletedProcess(args=[], returncode=returncode, stdout="", stderr=stderr)

    return _exec


def test_session_exists_when_tmux_succeeds(monkeypatch):
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(0))
    assert tmux.session_exists() is True


def test_absent_session_is_not_an_error(monkeypatch):
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(1, "no server running on /tmp/tmux-501/default"))
    assert tmux.session_exists() is False


@pytest.mark.parametrize(
    "stderr",
    [
        "couldn't create directory /private/tmp/tmux-501 (Operation not permitted)",
        "error creating /private/tmp/claude-501/tmux-501/default (Operation not permitted)",
        f"{SOCKET}: Permission denied",
    ],
)
def test_blocked_socket_raises_instead_of_reading_as_no_agents(monkeypatch, stderr):
    """A sandbox denial must not look like a session with no agents in it."""
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(1, stderr))
    with pytest.raises(bridge.BridgeError, match="cannot reach tmux"):
        tmux.session_exists()


def test_blocked_socket_error_points_at_the_settings_fix(monkeypatch):
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(1, "Operation not permitted"))
    with pytest.raises(bridge.BridgeError, match=r"tmux-and-sandbox\.md"):
        tmux.session_exists()


def test_blocked_socket_error_names_the_glob_mistake(monkeypatch):
    """Allowlist entries are literal subpath prefixes, so a trailing '/*' matches nothing real."""
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(1, "Operation not permitted"))
    with pytest.raises(bridge.BridgeError) as caught:
        tmux.session_exists()
    message = str(caught.value)
    assert "/*" in message
    assert "not globs" in message


# --- attach command ----------------------------------------------------------


def test_attach_command_default_socket():
    assert bridge.attach_command(bridge.Tmux()) == "tmux attach -t agents"


def test_attach_command_names_the_socket_so_the_human_can_match_it():
    tmux = bridge.Tmux(session="agents", socket=SOCKET)
    assert bridge.attach_command(tmux) == f"tmux -S {SOCKET} attach -t agents"


# --- argument parsing --------------------------------------------------------


def test_spawn_passes_args_after_the_separator_through_to_the_cli():
    args = bridge.build_parser().parse_args(["spawn", "api", "--model", "gpt-5.6-sol", "--", "--search"])
    assert args.model == "gpt-5.6-sol"
    assert args.agent_args == ["--search"]


def test_spawn_defaults_to_the_default_adapter():
    args = bridge.build_parser().parse_args(["spawn", "api"])
    assert args.agent == bridge.DEFAULT_ADAPTER


def test_spawn_rejects_an_unknown_agent():
    with pytest.raises(SystemExit):
        bridge.build_parser().parse_args(["spawn", "api", "--agent", "nonesuch"])


def test_spawn_rejects_cli_flags_without_the_separator():
    """An unrecognized flag is a typo until the caller marks it as passthrough."""
    with pytest.raises(SystemExit):
        bridge.build_parser().parse_args(["spawn", "api", "--search"])


def test_keys_accepts_multiple_key_names():
    args = bridge.build_parser().parse_args(["keys", "api", "Escape", "C-c"])
    assert args.keys == ["Escape", "C-c"]


def test_socket_comes_from_the_environment(monkeypatch):
    monkeypatch.setenv("AGENT_BRIDGE_SOCKET", SOCKET)
    args = bridge.build_parser().parse_args(["list"])
    assert args.socket == SOCKET


@pytest.mark.parametrize(
    "argv",
    [
        ["--json", "attach"],
        ["attach", "--json"],
    ],
)
def test_json_is_accepted_on_either_side_of_the_subcommand(argv):
    assert bridge.build_parser().parse_args(argv).json is True


def test_global_json_survives_a_subcommand_that_omits_it():
    """A subparser default must not reset a flag the top-level parser already set."""
    assert bridge.build_parser().parse_args(["--json", "list"]).json is True


def test_socket_is_accepted_after_the_subcommand():
    args = bridge.build_parser().parse_args(["attach", "--socket", SOCKET])
    assert args.socket == SOCKET


def test_attach_hands_over_the_command_even_when_the_socket_is_blocked(monkeypatch):
    """The human's terminal is not under the agent's sandbox, so the command is still useful."""
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(1, "Operation not permitted"))
    result = bridge.cmd_attach(tmux, argparse.Namespace())
    assert result["attach"] == "tmux attach -t agents"
    assert result["running"] is None
    assert "cannot reach tmux" in result["note"]


def test_a_dead_server_is_not_reported_as_an_empty_session(monkeypatch):
    """A stopped server described as an idle session hides that there is nothing to control."""
    tmux = bridge.Tmux()
    monkeypatch.setattr(
        tmux, "_exec", fake_exec(1, "error connecting to /private/tmp/tmux-501/default (No such file or directory)")
    )
    result = bridge.cmd_list(tmux, argparse.Namespace())
    assert result["status"] == "no-server"
    assert "no tmux server is running" in bridge.render(result, "list")


def test_no_server_running_is_also_recognised(monkeypatch):
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(1, "no server running on /private/tmp/tmux-501/default"))
    assert tmux.server_running() is False


def test_a_live_server_without_the_session_is_distinguished(monkeypatch):
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(1, "can't find session: agents"))
    result = bridge.cmd_list(tmux, argparse.Namespace())
    assert result["status"] == "no-session"
    assert "no session named" in bridge.render(result, "list")


def test_a_refused_socket_still_raises_rather_than_reporting_no_server(monkeypatch):
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(1, "Operation not permitted"))
    with pytest.raises(bridge.BridgeError, match="cannot reach tmux"):
        tmux.server_running()


def test_attach_reports_a_running_session(monkeypatch):
    tmux = bridge.Tmux()
    monkeypatch.setattr(tmux, "_exec", fake_exec(0))
    result = bridge.cmd_attach(tmux, argparse.Namespace())
    assert result["running"] is True
    assert "note" not in result


# --- session ownership -------------------------------------------------------


def scripted_tmux(
    monkeypatch,
    session_exists: bool,
    windows: list[dict],
    *,
    server_path: str | None = "/usr/bin",
) -> tuple[bridge.Tmux, list[list[str]]]:
    """Return a `Tmux` with stubbed state, plus the list that records commands it ran.

    `new-window -P` and `new-session -P` print the new window id, and the spawn path reads the
    server environment, so the stub answers both.
    """
    tmux = bridge.Tmux()
    ran: list[list[str]] = []

    monkeypatch.setattr(tmux, "session_exists", lambda: session_exists)
    monkeypatch.setattr(tmux, "windows", lambda: windows)

    def _run(*args, stdin=None):
        ran.append(list(args))
        if args[0] in {"new-window", "new-session"}:
            return "@1\n"
        if args[0] == "show-environment":
            if server_path is None:
                raise bridge.BridgeError("no such environment variable")
            return f"{args[2]}={server_path}\n"
        if args[0] == "display-message":
            return "1\n"
        return ""

    monkeypatch.setattr(tmux, "run", _run)
    return tmux, ran


def creations(ran: list[list[str]]) -> list[list[str]]:
    """Return only the window-creating commands, ignoring environment probes."""
    return [cmd for cmd in ran if cmd and cmd[0] in {"new-window", "new-session"}]


def spawn_args(**kwargs) -> argparse.Namespace:
    """Build a namespace with the fields `cmd_spawn` reads."""
    defaults = {
        "name": "api",
        "agent": "codex",
        "cd": None,
        "model": None,
        "prompt": None,
        "agent_args": [],
        "i_accept_unattended_risk": False,
        "create_session": False,
    }
    return argparse.Namespace(**{**defaults, **kwargs})


def test_spawn_refuses_to_create_the_session(monkeypatch):
    """The server's owner decides what sandbox every agent inherits, so the user starts it."""
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, ran = scripted_tmux(monkeypatch, session_exists=False, windows=[])
    with pytest.raises(bridge.BridgeError, match="tmux new-session -s agents"):
        bridge.cmd_spawn(tmux, spawn_args())
    assert not creations(ran)


def test_spawn_refusal_explains_the_sandbox_inheritance(monkeypatch):
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, _ = scripted_tmux(monkeypatch, session_exists=False, windows=[])
    with pytest.raises(bridge.BridgeError, match="sandbox"):
        bridge.cmd_spawn(tmux, spawn_args())


def test_spawn_creates_the_session_only_when_told_to(monkeypatch):
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, ran = scripted_tmux(monkeypatch, session_exists=False, windows=[])
    monkeypatch.setattr(tmux, "window_id", lambda _: "@1")
    result = bridge.cmd_spawn(tmux, spawn_args(create_session=True))
    assert result["created_session"] is True
    assert creations(ran)[0][0] == "new-session"


def test_spawn_reuses_an_existing_session(monkeypatch):
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    monkeypatch.setattr(tmux, "window_id", lambda _: "@1")
    result = bridge.cmd_spawn(tmux, spawn_args())
    assert result["created_session"] is False
    assert creations(ran)[0][0] == "new-window"


def test_spawn_records_the_cli_on_its_window(monkeypatch):
    """The tag marks the window as this script's and tells `send` which key submits."""
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/claude")
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    monkeypatch.setattr(tmux, "window_id", lambda _: "@1")
    result = bridge.cmd_spawn(tmux, spawn_args(agent="claude"))
    assert result["cli"] == "claude"
    assert ["set-option", "-w", "-t", "@1", bridge.MANAGED_OPTION, "claude"] in ran


def test_spawn_configures_the_window_before_starting_the_cli(monkeypatch):
    """A CLI that exits at once is reaped before a later set-option lands, losing its error."""
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    bridge.cmd_spawn(tmux, spawn_args())

    order = [cmd[0] for cmd in ran]
    assert order.index("new-window") < order.index("set-option")
    assert order.index("set-option") < order.index("respawn-pane")
    # The window is created empty; the agent arrives only with respawn-pane.
    creation = creations(ran)[0]
    assert not any(arg.startswith("codex") for arg in creation)


def test_spawn_checks_the_binary_against_the_server_path(monkeypatch):
    """Agents are forked by the tmux server, so its PATH is the one that decides."""
    seen: dict = {}
    monkeypatch.setattr(
        bridge.shutil, "which", lambda binary, path=None: seen.update(binary=binary, path=path) or "/x"
    )
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=[], server_path="/server/bin")
    bridge.cmd_spawn(tmux, spawn_args())
    assert seen["path"] == "/server/bin"


def test_spawn_falls_back_when_the_server_path_is_unreadable(monkeypatch):
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=[], server_path=None)
    result = bridge.cmd_spawn(tmux, spawn_args())
    assert result["cli"] == "codex"


def test_spawn_runs_the_adapters_binary(monkeypatch):
    seen = []
    monkeypatch.setattr(bridge.shutil, "which", lambda binary, path=None: seen.append(binary) or "/usr/bin/x")
    tmux, _ran = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    monkeypatch.setattr(tmux, "window_id", lambda _: "@1")
    result = bridge.cmd_spawn(tmux, spawn_args(agent="cursor"))
    assert seen == ["cursor-agent"]
    assert result["command"].startswith("cursor-agent")


def test_spawn_sets_the_working_directory_through_tmux(monkeypatch, tmp_path):
    """tmux sets the pane's cwd, so no per-CLI working-directory flag is needed."""
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    monkeypatch.setattr(tmux, "window_id", lambda _: "@1")
    result = bridge.cmd_spawn(tmux, spawn_args(cd=str(tmp_path)))
    created = creations(ran)[0]
    assert "-c" in created
    assert created[created.index("-c") + 1] == str(tmp_path.resolve())
    assert "--cd" not in result["command"]


def test_spawn_rejects_a_missing_working_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    monkeypatch.setattr(tmux, "window_id", lambda _: "@1")
    with pytest.raises(bridge.BridgeError, match="not a directory"):
        bridge.cmd_spawn(tmux, spawn_args(cd=str(tmp_path / "absent")))


def test_spawn_passes_a_positional_prompt(monkeypatch):
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/codex")
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    monkeypatch.setattr(tmux, "window_id", lambda _: "@1")
    result = bridge.cmd_spawn(tmux, spawn_args(prompt="read the tests"))
    assert result["command"].endswith("'read the tests'")


def test_spawn_refuses_a_prompt_it_cannot_place(monkeypatch):
    """Guessing an initial-prompt flag risks a headless run that exits instead of a live TUI."""
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: "/usr/bin/copilot")
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    monkeypatch.setattr(tmux, "window_id", lambda _: "@1")
    with pytest.raises(bridge.BridgeError, match="send"):
        bridge.cmd_spawn(tmux, spawn_args(agent="copilot", prompt="go"))


def test_spawn_reports_a_missing_binary(monkeypatch):
    monkeypatch.setattr(bridge.shutil, "which", lambda _binary, path=None: None)
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=[])
    with pytest.raises(bridge.BridgeError, match="gemini is not on the tmux server's PATH"):
        bridge.cmd_spawn(tmux, spawn_args(agent="gemini"))


def test_kill_all_spares_windows_the_user_opened(monkeypatch):
    windows = [
        {"id": "@0", "name": "zsh", "pid": "1", "state": "running", "cli": "", "owner": ""},
        {"id": "@1", "name": "api", "pid": "2", "state": "running", "cli": "codex", "owner": ""},
        {"id": "@2", "name": "docs", "pid": "3", "state": "dead", "cli": "claude", "owner": ""},
    ]
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    result = bridge.cmd_kill(tmux, argparse.Namespace(all=True, name=[], any_owner=False))
    assert result["killed"] == ["api", "docs"]
    assert result["kept"] == ["zsh"]
    assert ["kill-window", "-t", "@0"] not in ran


def test_kill_all_never_kills_the_session(monkeypatch):
    """The session belongs to the user; tearing it down takes their terminal state with it."""
    windows = [{"id": "@1", "name": "api", "pid": "2", "state": "running", "cli": "codex", "owner": ""}]
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    bridge.cmd_kill(tmux, argparse.Namespace(all=True, name=[], any_owner=False))
    assert all(cmd[0] != "kill-session" for cmd in ran)


def test_kill_all_on_a_missing_session_is_not_an_error(monkeypatch):
    tmux, _ = scripted_tmux(monkeypatch, session_exists=False, windows=[])
    result = bridge.cmd_kill(tmux, argparse.Namespace(all=True, name=[], any_owner=False))
    assert result["killed"] == []


# --- owner resolution --------------------------------------------------------


def test_owner_defaults_to_the_git_repository_root(monkeypatch, tmp_path):
    monkeypatch.delenv("AGENT_BRIDGE_OWNER", raising=False)
    monkeypatch.setattr(
        bridge.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(args=[], returncode=0, stdout=f"{tmp_path}\n", stderr=""),
    )
    assert bridge.default_owner() == str(tmp_path)


def test_owner_falls_back_to_the_working_directory_outside_a_repo(monkeypatch):
    monkeypatch.delenv("AGENT_BRIDGE_OWNER", raising=False)
    monkeypatch.setattr(
        bridge.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(args=[], returncode=128, stdout="", stderr="not a repo"),
    )
    assert bridge.default_owner() == str(Path.cwd().resolve())


def test_owner_can_be_set_explicitly(monkeypatch):
    monkeypatch.setenv("AGENT_BRIDGE_OWNER", "/projects/thing")
    assert bridge.default_owner() == "/projects/thing"


def test_owner_is_shown_by_its_basename():
    """The full path keeps two repositories with the same name apart; the label stays readable."""
    assert bridge.owner_label("/Users/someone/code/skills") == "skills"


def test_kill_all_leaves_another_projects_agents(monkeypatch):
    windows = [
        {"id": "@1", "name": "mine", "pid": "2", "state": "running", "cli": "codex", "owner": "/a"},
        {"id": "@2", "name": "theirs", "pid": "3", "state": "running", "cli": "codex", "owner": "/b"},
    ]
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    monkeypatch.setattr(tmux, "owner", "/a")
    result = bridge.cmd_kill(tmux, argparse.Namespace(all=True, name=[], any_owner=False))
    assert result["killed"] == ["mine"]
    assert result["kept"] == ["theirs"]
    assert ["kill-window", "-t", "@2"] not in ran


def test_any_owner_widens_the_teardown(monkeypatch):
    windows = [
        {"id": "@1", "name": "mine", "pid": "2", "state": "running", "cli": "codex", "owner": "/a"},
        {"id": "@2", "name": "theirs", "pid": "3", "state": "running", "cli": "codex", "owner": "/b"},
    ]
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    monkeypatch.setattr(tmux, "owner", "/a")
    result = bridge.cmd_kill(tmux, argparse.Namespace(all=True, name=[], any_owner=True))
    assert result["killed"] == ["mine", "theirs"]


def test_untagged_owner_windows_stay_killable(monkeypatch):
    """Agents spawned before owners were recorded still answer to their own controller."""
    windows = [{"id": "@1", "name": "old", "pid": "2", "state": "running", "cli": "codex", "owner": ""}]
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    result = bridge.cmd_kill(tmux, argparse.Namespace(all=True, name=[], any_owner=False))
    assert result["killed"] == ["old"]


def test_send_refuses_another_projects_agent(monkeypatch):
    windows = [{"id": "@1", "name": "api", "pid": "2", "state": "running", "cli": "codex", "owner": "/b"}]
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    monkeypatch.setattr(tmux, "owner", "/a")
    with pytest.raises(bridge.BridgeError, match="was spawned for"):
        bridge.cmd_send(tmux, send_args())
    assert all(cmd[0] not in {"paste-buffer", "send-keys"} for cmd in ran)


def test_session_defaults_to_agents():
    assert bridge.build_parser().parse_args(["list"]).session == "agents"


# --- submit keys -------------------------------------------------------------


def send_args(**kwargs) -> argparse.Namespace:
    """Build a namespace with the fields `cmd_send` reads."""
    defaults = {
        "name": "api",
        "text": ["run the tests"],
        "file": None,
        "no_submit": False,
        "submit_delay": 0.0,
        "submit_key": None,
        "any_owner": False,
    }
    return argparse.Namespace(**{**defaults, **kwargs})


def test_send_uses_the_key_recorded_for_the_window(monkeypatch):
    windows = [{"id": "@1", "name": "api", "pid": "2", "state": "running", "cli": "codex", "owner": ""}]
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    result = bridge.cmd_send(tmux, send_args())
    assert result["submit_key"] == bridge.ADAPTERS["codex"].submit_key
    assert ["send-keys", "-t", "@1", result["submit_key"]] in ran


UNTAGGED_SHELL = [{"id": "@0", "name": "zsh", "pid": "1", "state": "running", "cli": "", "owner": ""}]
"""A window the user opened, such as the shell tmux starts a session with."""


def test_send_refuses_a_window_the_script_did_not_spawn(monkeypatch):
    """A paste plus Enter into the user's shell runs as a command, not as a message."""
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=UNTAGGED_SHELL)
    with pytest.raises(bridge.BridgeError, match="did not spawn"):
        bridge.cmd_send(tmux, send_args(name="zsh"))
    assert all(cmd[0] not in {"paste-buffer", "send-keys"} for cmd in ran)


def test_keys_refuses_a_window_the_script_did_not_spawn(monkeypatch):
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=UNTAGGED_SHELL)
    with pytest.raises(bridge.BridgeError, match="did not spawn"):
        bridge.cmd_keys(tmux, argparse.Namespace(name="zsh", keys=["C-c"], any_owner=False))
    assert ran == []


def test_named_kill_refuses_a_window_the_script_did_not_spawn(monkeypatch):
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=UNTAGGED_SHELL)
    with pytest.raises(bridge.BridgeError, match="did not spawn"):
        bridge.cmd_kill(tmux, argparse.Namespace(all=False, name=["zsh"], any_owner=False))
    assert ran == []


def test_peek_is_allowed_on_a_window_the_script_did_not_spawn(monkeypatch):
    """Capturing delivers nothing to the pane, so reading stays available for diagnosis."""
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=UNTAGGED_SHELL)
    result = bridge.cmd_peek(tmux, argparse.Namespace(name="zsh", lines=0, history=0))
    assert result["window"] == "@0"


def test_send_submit_key_can_be_overridden(monkeypatch):
    windows = [{"id": "@1", "name": "api", "pid": "2", "state": "running", "cli": "codex", "owner": ""}]
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    result = bridge.cmd_send(tmux, send_args(submit_key="M-Enter"))
    assert result["submit_key"] == "M-Enter"
    assert ["send-keys", "-t", "@1", "M-Enter"] in ran


def test_send_pastes_with_bracketed_paste(monkeypatch):
    """Without -p, each newline reaches the composer as Enter and submits a fragment."""
    windows = [{"id": "@1", "name": "api", "pid": "2", "state": "running", "cli": "codex", "owner": ""}]
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    bridge.cmd_send(tmux, send_args(text=["line one\nline two"]))
    paste = next(cmd for cmd in ran if cmd[0] == "paste-buffer")
    assert "-p" in paste


def test_send_refuses_an_empty_message(monkeypatch):
    windows = [{"id": "@1", "name": "api", "pid": "2", "state": "running", "cli": "codex", "owner": ""}]
    tmux, _ = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    with pytest.raises(bridge.BridgeError, match="empty message"):
        bridge.cmd_send(tmux, send_args(text=["   "]))


def test_no_submit_skips_the_key(monkeypatch):
    windows = [{"id": "@1", "name": "api", "pid": "2", "state": "running", "cli": "codex", "owner": ""}]
    tmux, ran = scripted_tmux(monkeypatch, session_exists=True, windows=windows)
    result = bridge.cmd_send(tmux, send_args(no_submit=True))
    assert result["submitted"] is False
    assert all(cmd[0] != "send-keys" for cmd in ran)


def test_a_subcommand_is_required():
    with pytest.raises(SystemExit):
        bridge.build_parser().parse_args([])


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    sys.exit(pytest.main([__file__, "-v", "--rootdir", here, "--confcutdir", here]))
