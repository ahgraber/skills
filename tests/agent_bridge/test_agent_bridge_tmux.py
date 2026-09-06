#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8.0",
# ]
# ///
"""Integration tests for `agent_bridge.py` against a real tmux server.

The unit tests stub every tmux call, which cannot catch a format string tmux rejects, an
option that does not survive a round trip, or an ordering bug that only loses a race against a
real process. Those are the defects this file exists to catch.

By default each test starts its own tmux server on a scratch socket and kills it afterwards,
so it never touches a session a person is using. The stand-in for an agent CLI is `cat`: it
stays alive holding its input open, which is the only behavior of a TUI these tests depend on.

Set `AGENT_BRIDGE_TEST_SOCKET` to borrow a server someone else started. That is the only way to
run these tests from a sandboxed process: a server started from one inherits the sandbox and
fails every window with `fork failed`. Teardown then removes just this module's own session.

    AGENT_BRIDGE_TEST_SOCKET=/private/tmp/tmux-$(id -u)/default uv run tests/agent_bridge/test_agent_bridge_tmux.py

The module skips rather than fails whenever no usable server is available, because that is a
missing precondition, not a defect in the code under test.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "agent-bridge" / "scripts" / "agent_bridge.py"

_spec = importlib.util.spec_from_file_location("bridge_integration", SCRIPT)
assert _spec is not None
assert _spec.loader is not None
bridge = importlib.util.module_from_spec(_spec)
sys.modules["bridge_integration"] = bridge
_spec.loader.exec_module(bridge)


def socket_path() -> str:
    """Return a scratch socket beside tmux's own directory for this user.

    tmux's per-uid directory is the one a sandbox is most likely to permit, so a scratch socket
    inside it runs in the same environments the skill itself runs in.
    """
    directory = Path(f"/tmp/tmux-{os.getuid()}")  # noqa: S108
    directory.mkdir(mode=0o700, exist_ok=True)
    return str(directory / f"agent-bridge-test-{uuid.uuid4().hex[:8]}.sock")


def tmux_usable(socket: str) -> str:
    """Return an empty string when a usable server can run here, or the reason it cannot.

    Starting a server is not enough to know these tests can run. A server started from a
    sandboxed process inherits that sandbox, and a sandbox that denies pty allocation lets the
    server start and then fails every window with `fork failed`. The probe therefore creates a
    window, which is the operation every test here depends on.
    """
    if shutil.which("tmux") is None:
        return "tmux is not installed"
    probe = subprocess.run(  # noqa: S603
        ["tmux", "-S", socket, "-f", "/dev/null", "new-session", "-d", "-s", "probe", "true"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        return (probe.stderr or "tmux could not create a window").strip()
    subprocess.run(  # noqa: S603
        ["tmux", "-S", socket, "kill-server"],
        capture_output=True,
        check=False,
    )
    return ""


FAKE = bridge.Adapter(
    name="fake",
    binary="cat",
    prompt_flag=bridge.PROMPT_UNSUPPORTED,
    config_hint="",
)
"""An adapter that runs `cat` instead of an agent CLI.

Spawning a real agent in a test would need credentials, spend tokens, and make the result
depend on a model's behavior. Every property under test here is a property of the tmux
plumbing, which does not care what the pane runs.
"""


SESSION = "agent-bridge-test"
"""Session name these tests create. Distinct so a borrowed server keeps its other sessions."""

EXTERNAL_SOCKET = os.environ.get("AGENT_BRIDGE_TEST_SOCKET")
"""Point the tests at an already-running server instead of starting one.

A server started from a sandboxed process inherits that sandbox and cannot fork panes, so in
those environments the only server that works is one someone else started. Teardown then
removes this module's own session and leaves the server and its other sessions alone.
"""


@pytest.fixture
def server(monkeypatch):
    """Yield a `Tmux` bound to a usable server, and remove what the test created."""
    socket = EXTERNAL_SOCKET or socket_path()
    if EXTERNAL_SOCKET:
        # A borrowed server that is not running is a missing precondition, not a failure.
        probe = subprocess.run(  # noqa: S603
            ["tmux", "-S", socket, "list-sessions"],
            capture_output=True,
            text=True,
            check=False,
        )
        if probe.returncode != 0:
            pytest.skip(f"no server on {socket}: {(probe.stderr or '').strip()}")
    else:
        reason = tmux_usable(socket)
        if reason:
            pytest.skip(f"no usable tmux server: {reason}")

    monkeypatch.setitem(bridge.ADAPTERS, "fake", FAKE)
    tmux = bridge.Tmux(session=SESSION, socket=socket)
    try:
        yield tmux
    finally:
        if EXTERNAL_SOCKET:
            # Borrowed server: take only this module's session with it.
            subprocess.run(  # noqa: S603
                ["tmux", "-S", socket, "kill-session", "-t", f"={SESSION}"],
                capture_output=True,
                check=False,
            )
        else:
            subprocess.run(  # noqa: S603
                ["tmux", "-S", socket, "kill-server"],
                capture_output=True,
                check=False,
            )
            Path(socket).unlink(missing_ok=True)


def spawn_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "name": "worker",
        "agent": "fake",
        "cd": None,
        "model": None,
        "prompt": None,
        "agent_args": [],
        "i_accept_unattended_risk": False,
        "create_session": True,
    }
    return argparse.Namespace(**{**defaults, **kwargs})


def send_args(**kwargs) -> argparse.Namespace:
    defaults = {
        "name": "worker",
        "text": ["hello"],
        "file": None,
        "no_submit": False,
        "submit_delay": 0.05,
        "submit_key": None,
        "any_owner": False,
    }
    return argparse.Namespace(**{**defaults, **kwargs})


def test_spawn_creates_a_window_a_real_server_reports(server):
    result = bridge.cmd_spawn(server, spawn_args())
    assert result["created_session"] is True
    names = [w["name"] for w in server.windows()]
    assert names == ["worker"]


def test_the_managed_tag_survives_a_round_trip(server):
    """The tag is read back through a tmux format string, which the unit tests cannot check."""
    bridge.cmd_spawn(server, spawn_args())
    window = next(w for w in server.windows() if w["name"] == "worker")
    assert window["cli"] == "fake"


def test_list_windows_format_parses_against_real_output(server):
    bridge.cmd_spawn(server, spawn_args())
    window = next(w for w in server.windows() if w["name"] == "worker")
    assert window["id"].startswith("@")
    assert window["pid"].isdigit()
    assert window["state"] == "running"


def test_a_window_the_user_opened_reads_back_untagged(server):
    bridge.cmd_spawn(server, spawn_args())
    server.run("new-window", "-d", "-t", f"={server.session}:", "-n", "mine", "cat")
    window = next(w for w in server.windows() if w["name"] == "mine")
    assert window["cli"] == ""


def test_send_refuses_a_real_untagged_window(server):
    """The failure this prevents is a paste and Enter running as a command in the user's shell."""
    bridge.cmd_spawn(server, spawn_args())
    server.run("new-window", "-d", "-t", f"={server.session}:", "-n", "mine", "cat")
    with pytest.raises(bridge.BridgeError, match="did not spawn"):
        bridge.cmd_send(server, send_args(name="mine"))


def test_a_fast_exiting_command_leaves_a_readable_window(server):
    """remain-on-exit has to be set before the command runs, or tmux reaps the window first."""
    bridge.cmd_spawn(server, spawn_args(name="dies", agent_args=["/nonexistent-path-for-this-test"]))
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        windows = {w["name"]: w for w in server.windows()}
        if "dies" in windows and windows["dies"]["state"] == "dead":
            break
        time.sleep(0.1)
    windows = {w["name"]: w for w in server.windows()}
    assert "dies" in windows, "the window was reaped before it could be inspected"
    assert windows["dies"]["state"] == "dead"


def test_a_multi_line_message_arrives_as_one_paste(server):
    """Without bracketed paste each newline reaches the pane as Enter and splits the message."""
    bridge.cmd_spawn(server, spawn_args())
    time.sleep(0.3)
    bridge.cmd_send(server, send_args(text=["first line\nsecond line"]))
    time.sleep(0.5)

    window = server.window_id("worker", managed_only=False)
    screen = bridge.capture(server, window)
    assert "first line" in screen
    assert "second line" in screen


def test_kill_all_removes_agents_and_keeps_user_windows(server):
    bridge.cmd_spawn(server, spawn_args())
    server.run("new-window", "-d", "-t", f"={server.session}:", "-n", "mine", "cat")

    result = bridge.cmd_kill(server, argparse.Namespace(all=True, name=[], any_owner=False))
    assert result["killed"] == ["worker"]
    assert result["kept"] == ["mine"]
    assert [w["name"] for w in server.windows()] == ["mine"]


def test_the_watch_command_names_the_window_index(server):
    result = bridge.cmd_spawn(server, spawn_args())
    assert "Ctrl-b" in result["watch"]
    assert result["watch"].startswith("tmux -S")


def test_session_exists_is_false_before_anything_is_created(server):
    assert server.session_exists() is False


# --- several controllers sharing one session ---------------------------------


def other_controller(server) -> bridge.Tmux:
    """Return a second controller on the same session, speaking for a different project."""
    return bridge.Tmux(session=server.session, socket=server.socket, owner="/projects/somewhere-else")


def test_the_owner_survives_a_round_trip(server):
    bridge.cmd_spawn(server, spawn_args())
    window = next(w for w in server.windows() if w["name"] == "worker")
    assert window["owner"] == server.owner


def test_another_controller_cannot_send_to_these_agents(server):
    bridge.cmd_spawn(server, spawn_args())
    with pytest.raises(bridge.BridgeError, match="was spawned for"):
        bridge.cmd_send(other_controller(server), send_args())


def test_another_controller_cannot_kill_these_agents_by_name(server):
    bridge.cmd_spawn(server, spawn_args())
    with pytest.raises(bridge.BridgeError, match="was spawned for"):
        bridge.cmd_kill(other_controller(server), argparse.Namespace(all=False, name=["worker"], any_owner=False))
    assert "worker" in [w["name"] for w in server.windows()]


def test_kill_all_leaves_another_controllers_agents_running(server):
    """A teardown that reached every managed window would end another project's work mid-task."""
    bridge.cmd_spawn(server, spawn_args())
    result = bridge.cmd_kill(other_controller(server), argparse.Namespace(all=True, name=[], any_owner=False))
    assert result["killed"] == []
    assert result["kept"] == ["worker"]
    assert "worker" in [w["name"] for w in server.windows()]


def test_kill_all_takes_its_own_agents(server):
    bridge.cmd_spawn(server, spawn_args())
    result = bridge.cmd_kill(server, argparse.Namespace(all=True, name=[], any_owner=False))
    assert result["killed"] == ["worker"]


def test_any_owner_reaches_across_projects_when_asked(server):
    bridge.cmd_spawn(server, spawn_args())
    result = bridge.cmd_kill(other_controller(server), argparse.Namespace(all=True, name=[], any_owner=True))
    assert result["killed"] == ["worker"]


def test_reading_another_controllers_agent_is_allowed(server):
    """Seeing what a shared session is doing is the point; only writing is scoped."""
    bridge.cmd_spawn(server, spawn_args())
    result = bridge.cmd_peek(other_controller(server), argparse.Namespace(name="worker", lines=0, history=0))
    assert result["agent"] == "worker"


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    sys.exit(pytest.main([__file__, "-v", "--rootdir", here, "--confcutdir", here]))
