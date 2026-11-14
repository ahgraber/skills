#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = []
# ///
"""List the jj commands run since an operation, from the op log.

The teach-mode turn report is built from this list rather than from memory,
so no command the agent ran is omitted. By default snapshot operations and
read-only commands are dropped; `--all` keeps them. The op log is shared by
every workspace of the repo and also records the human's own commands, so
`--workspace` narrows the list to one workspace, and the agent still drops
any command it did not run.

    uv run --quiet jj_turn_log.py --since OPID [--repo PATH] [--workspace NAME] [--all] [--format json|text]

stdout: a JSON array (oldest first) of objects with `op_id`, `time`,
`workspace`, `command`, `subcommand`, `description`, `snapshot`, and
`mutating`; or one line per operation with `--format text`.

Exit codes: 0 success; 1 the op log could not be read; 2 the `--since`
operation is not in the log.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys

JJ_FLAGS = ("--no-pager", "--color=never")
# One record per operation, NUL-terminated, because a command's arguments can
# contain newlines (a multi-line -m message) but never a NUL.
RECORD_SEP = "\0"
FIELD_SEP = "\t"
OP_TEMPLATE = (
    'id.short(12) ++ "\\t" ++ snapshot ++ "\\t" ++ time.start().format("%Y-%m-%dT%H:%M:%S")'
    ' ++ "\\t" ++ self.workspace_name() ++ "\\t" ++ description.first_line() ++ "\\t" ++ self.attributes() ++ "\\0"'
)
ARGS_PREFIX = "args: "

# Global flags that take a value, so the token after them is not the subcommand.
GLOBAL_FLAGS_WITH_VALUE = {
    "--config",
    "--config-file",
    "--config-toml",
    "-R",
    "--repository",
    "--at-op",
    "--at-operation",
    "--color",
}

READ_ONLY = {
    "st",
    "status",
    "log",
    "diff",
    "show",
    "evolog",
    "obslog",
    "interdiff",
    "root",
    "help",
    "version",
}
READ_ONLY_SUB = {
    "op": {"log", "show", "diff"},
    "file": {"show", "list", "annotate"},
    "bookmark": {"list"},
    "workspace": {"list", "root"},
    "config": {"get", "list", "path"},
    "git": {"remote"},
}

# Commands whose first positional word is itself a subcommand (`jj op revert`, `jj git push`).
GROUP_COMMANDS = {"op", "file", "bookmark", "workspace", "config", "git", "util"}

EXIT_OK = 0
EXIT_LOG_FAILED = 1
EXIT_SINCE_MISSING = 2

Runner = Callable[[list[str], Path | None], tuple[int, str, str]]


def run_jj(args: list[str], cwd: Path | None) -> tuple[int, str, str]:
    """Run one jj command headless and return (exit code, stdout, stderr)."""
    env = dict(os.environ, JJ_EDITOR="false")
    proc = subprocess.run(  # noqa: S603 - args are built by this script, not from untrusted text
        ["jj", *JJ_FLAGS, *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
        check=False,
    )
    return proc.returncode, proc.stdout, proc.stderr


@dataclass
class Operation:
    op_id: str
    time: str
    workspace: str
    command: str
    subcommand: str
    description: str
    snapshot: bool
    mutating: bool


def split_subcommand(command: str) -> tuple[str, str]:
    """Return (subcommand, group member) for a recorded `jj ...` command line.

    The second word is filled only for group commands such as `jj op revert`;
    for `jj describe -m text` it stays empty, because the word after a flag is
    that flag's value, not a subcommand.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        tokens = command.split()
    skip_next = False
    first = ""
    second = ""
    for token in tokens[1:]:
        if skip_next:
            skip_next = False
            continue
        if token in GLOBAL_FLAGS_WITH_VALUE:
            skip_next = True
            continue
        if token.startswith("-"):
            continue
        if not first:
            first = token
            if first not in GROUP_COMMANDS:
                break
            continue
        second = token
        break
    return first, second


def is_mutating(command: str) -> bool:
    """Report whether the command changes the repo, as opposed to only reading it."""
    first, second = split_subcommand(command)
    if first in READ_ONLY:
        return False
    if first in READ_ONLY_SUB and second in READ_ONLY_SUB[first]:
        return False
    return not (first == "resolve" and "--list" in command)


def parse_record(record: str) -> Operation | None:
    """Parse one NUL-terminated op log record produced by OP_TEMPLATE."""
    parts = record.split(FIELD_SEP, 5)
    if len(parts) < 6:
        return None
    op_id, snapshot, time, workspace, description, attributes = parts
    command = attributes.removeprefix(ARGS_PREFIX)
    subcommand = " ".join(w for w in split_subcommand(command) if w)
    return Operation(
        op_id=op_id,
        time=time,
        workspace=workspace.rstrip("@"),
        command=command,
        subcommand=subcommand,
        description=description,
        snapshot=snapshot == "true",
        mutating=is_mutating(command) if command else False,
    )


def operations_since(raw: str, since: str) -> list[Operation] | None:
    """Return the operations newer than `since`, oldest first, or None if `since` is absent."""
    collected: list[Operation] = []
    for record in raw.split(RECORD_SEP):
        if not record.strip():
            continue
        op = parse_record(record)
        if op is None:
            continue
        if op.op_id.startswith(since) or since.startswith(op.op_id):
            return list(reversed(collected))
        collected.append(op)
    return None


def select(ops: list[Operation], include_all: bool, workspace: str | None) -> list[Operation]:
    """Drop snapshots and read-only commands unless `include_all`; keep one workspace when named."""
    chosen = ops if include_all else [op for op in ops if op.mutating and not op.snapshot]
    if workspace:
        chosen = [op for op in chosen if op.workspace == workspace.rstrip("@")]
    return chosen


def render_text(ops: list[Operation]) -> str:
    """One line per operation for a human; a multi-line command keeps its newlines."""
    return "\n".join(f"{op.time}  {op.op_id}  {op.workspace}  {op.command}  -- {op.description}" for op in ops)


def main(argv: list[str] | None = None, runner: Runner = run_jj) -> int:
    """Parse arguments, read the op log, print the selection, and return the exit code."""
    parser = argparse.ArgumentParser(description="jj commands run since an operation, from the op log.")
    parser.add_argument(
        "--since", required=True, help="operation ID (prefix) reported by jj_preflight.py at the start of the turn"
    )
    parser.add_argument("--repo", default=".", help="directory inside the repo (default: current directory)")
    parser.add_argument(
        "--workspace", default=None, help="keep only operations from this workspace (as reported by jj_preflight.py)"
    )
    parser.add_argument("--all", action="store_true", help="keep snapshot operations and read-only commands")
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)

    code, out, err = runner(["op", "log", "--no-graph", "-T", OP_TEMPLATE], Path(args.repo))
    if code != 0:
        print(f"error: jj op log failed: {err.strip()}", file=sys.stderr)
        return EXIT_LOG_FAILED

    ops = operations_since(out, args.since)
    if ops is None:
        print(f"error: operation {args.since} is not in the op log", file=sys.stderr)
        return EXIT_SINCE_MISSING

    chosen = select(ops, args.all, args.workspace)
    if args.format == "json":
        print(json.dumps([asdict(op) for op in chosen], indent=2))
    else:
        print(render_text(chosen))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
