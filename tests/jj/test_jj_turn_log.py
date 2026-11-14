#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8.0.0",
# ]
# ///
"""Behavior tests for the jj skill's turn-log script.

The op log is supplied as fixed template output, so the tests assert the
selection, the ordering, the workspace filter, multi-line commands, and the
read-only classification without a repo.

Run: uv run tests/jj/test_jj_turn_log.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "skills" / "jj" / "scripts" / "jj_turn_log.py"
_spec = importlib.util.spec_from_file_location("jj_turn_log", _MODULE_PATH)
assert _spec is not None
assert _spec.loader is not None
tl = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = tl
_spec.loader.exec_module(tl)


def record(op_id: str, snapshot: str, time: str, workspace: str, description: str, args: str) -> str:
    return f"{op_id}\t{snapshot}\t{time}\t{workspace}\t{description}\t{args}\0"


# Newest first, as `jj op log` prints it.
OP_LOG = "".join(
    [
        record(
            "aaaa00000006",
            "false",
            "2026-10-09T10:06:00",
            "agent2@",
            "describe commit 9f9f9f9f",
            "args: jj describe -m 'other agent'",
        ),
        record(
            "aaaa00000005",
            "true",
            "2026-10-09T10:05:00",
            "default@",
            "snapshot working copy",
            "args: jj status --no-pager '--color=never'",
        ),
        record(
            "aaaa00000004",
            "false",
            "2026-10-09T10:04:00",
            "default@",
            "squash commits into 1a2b3c4d",
            "args: jj squash --into kxrp -u src/a.py",
        ),
        record(
            "aaaa00000003",
            "false",
            "2026-10-09T10:03:00",
            "default@",
            "new empty commit",
            "args: jj new -m 'feat(x): second step'",
        ),
        record(
            "aaaa00000002",
            "true",
            "2026-10-09T10:02:00",
            "default@",
            "snapshot working copy",
            "args: jj new -m 'feat(x): second step'",
        ),
        record(
            "aaaa00000001",
            "false",
            "2026-10-09T10:01:00",
            "default@",
            "describe commit 1a2b3c4d",
            "args: jj describe -m 'feat(x): first\n\nbody line'",
        ),
        record(
            "88ccc4bc882f",
            "true",
            "2026-10-09T10:00:00",
            "default@",
            "snapshot working copy",
            "args: jj status --no-pager",
        ),
        record("59e6c34b3b5e", "false", "2026-10-09T09:00:00", "default@", "add workspace 'default'", ""),
        record("000000000000", "false", "1970-01-01T00:00:00", "", "", ""),
    ]
)


def fake_runner(args: list[str], cwd: Path | None) -> tuple[int, str, str]:
    assert args[:2] == ["op", "log"]
    return 0, OP_LOG, ""


@pytest.mark.parametrize(
    ("command", "mutating"),
    [
        ("jj status --no-pager", False),
        ("jj log -r 'trunk()..@' --no-graph -T 'change_id'", False),
        ("jj --config ui.x=y diff --git", False),
        ("jj op log -n 5", False),
        ("jj file show -r @ a.py", False),
        ("jj bookmark list --all", False),
        ("jj resolve --list -r @", False),
        ("jj new -m 'feat: x'", True),
        ("jj describe -r kxrp -m 'x'", True),
        ("jj squash --into kxrp -u src/a.py", True),
        ("jj op revert aaaa", True),
        ("jj bookmark move feature --to @-", True),
        ("jj resolve --tool :ours a.py", True),
        ("jj --config-file agent.toml sign -r 'kxrp..@ & ~empty()'", True),
    ],
)
def test_read_only_classification(command: str, mutating: bool):
    assert tl.is_mutating(command) is mutating


def test_subcommand_skips_global_flags_and_flag_values():
    assert tl.split_subcommand("jj --config-file agent.toml sign -r x") == ("sign", "")
    assert tl.split_subcommand("jj -R /repo op revert aaaa") == ("op", "revert")
    assert tl.split_subcommand("jj describe -m 'feat: x'") == ("describe", "")
    assert tl.split_subcommand("jj git push --named f=@-") == ("git", "push")


def test_operations_since_is_exclusive_and_oldest_first():
    ops = tl.operations_since(OP_LOG, "88ccc4bc882f")
    assert ops is not None
    assert [op.op_id for op in ops] == [f"aaaa0000000{n}" for n in range(1, 7)]


def test_since_accepts_prefix():
    ops = tl.operations_since(OP_LOG, "88ccc4")
    assert ops is not None
    assert len(ops) == 6


def test_missing_since_returns_none():
    assert tl.operations_since(OP_LOG, "ffffffffffff") is None


def test_multiline_command_is_kept_whole():
    ops = tl.operations_since(OP_LOG, "88ccc4bc882f")
    assert ops is not None
    assert ops[0].command == "jj describe -m 'feat(x): first\n\nbody line'"
    assert ops[0].subcommand == "describe"


def test_select_drops_snapshots_and_read_only_and_filters_workspace():
    ops = tl.operations_since(OP_LOG, "88ccc4bc882f")
    assert ops is not None
    chosen = tl.select(ops, include_all=False, workspace=None)
    assert [op.subcommand for op in chosen] == ["describe", "new", "squash", "describe"]
    mine = tl.select(ops, include_all=False, workspace="default")
    assert [op.command for op in mine] == [
        "jj describe -m 'feat(x): first\n\nbody line'",
        "jj new -m 'feat(x): second step'",
        "jj squash --into kxrp -u src/a.py",
    ]
    assert tl.select(ops, include_all=False, workspace="default@") == mine
    assert len(tl.select(ops, include_all=True, workspace=None)) == 6


def test_main_json_and_exit_codes(capsys: pytest.CaptureFixture[str]):
    code = tl.main(["--since", "88ccc4bc882f", "--workspace", "default"], runner=fake_runner)
    out = json.loads(capsys.readouterr().out)
    assert code == tl.EXIT_OK
    assert [op["subcommand"] for op in out] == ["describe", "new", "squash"]
    assert out[0]["workspace"] == "default"

    code = tl.main(["--since", "ffff"], runner=fake_runner)
    assert code == tl.EXIT_SINCE_MISSING

    def broken(args: list[str], cwd: Path | None) -> tuple[int, str, str]:
        return 1, "", "Error: no repo\n"

    assert tl.main(["--since", "88cc"], runner=broken) == tl.EXIT_LOG_FAILED


def test_text_format_one_record_per_op(capsys: pytest.CaptureFixture[str]):
    code = tl.main(["--since", "88ccc4bc882f", "--workspace", "default", "--format", "text"], runner=fake_runner)
    out = capsys.readouterr().out
    assert code == tl.EXIT_OK
    assert out.count("  -- ") == 3
    assert "body line'  -- describe commit 1a2b3c4d" in out


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    sys.exit(pytest.main([str(Path(__file__)), "--rootdir", str(here), "--confcutdir", str(here), "-q"]))
