#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = []
# ///
"""Orient checks for the `jj` skill.

Runs the checks an agent needs before it touches a jj repository and prints one
JSON object to stdout. Diagnostics go to stderr.

    uv run --quiet jj_preflight.py [--repo PATH] [--agent-config PATH] [--format json|text]

Checks: jj is installed at or above the version floor; the directory is a jj
repo; the repo is colocated with git; `user.name` and `user.email` are set;
the agent signing config exists, names a backend, and points at a key that
exists; `immutable_heads()` includes remote bookmarks; conflict markers are
git style; an in-repo `.worktrees/` directory is git-ignored; the teach flag
is present in a project instruction file; the state of `@`; the base of the
agent's stack; the nearest bookmarks and trunk; the current workspace and
operation ID.

The base is the change the agent's work sits on: `@` when the agent will start
with `jj new`, or `@-` when `@` is empty and undescribed and the agent will
describe it. Every revset that must cover only the agent's changes is
`<base>..@`.

Exit codes: 0 all checks passed (warnings allowed); 1 a setup item failed;
2 jj is missing or this is not a jj repo; 3 `@` holds edits with no
description and the human must decide what to do with them.

Running this snapshots the working copy, which is intended: it records the
human's edits into `@` before the agent changes anything.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

import tomllib

MIN_VERSION = (0, 41, 0)
JJ_FLAGS = ("--no-pager", "--color=never")
TEACH_FILES = ("AGENTS.md", "CLAUDE.md", "CLAUDE.local.md")
TEACH_LINE = re.compile(r"^\s*jj:\s*teach\s*$", re.IGNORECASE)
DEFAULT_AGENT_CONFIG = Path("~/.config/jj/agent.toml")
SIGNING_BACKENDS = ("ssh", "gpg", "gpgsm")
REMOTE_BOOKMARKS_ALIAS = re.compile(r"(?<![A-Za-z_])remote_bookmarks\(\)")
WORKTREES_DIR = ".worktrees"
WORKING_COPY_TEMPLATE = (
    'change_id.short() ++ "\\t" ++ commit_id.short() ++ "\\t" ++ empty ++ "\\t" ++ conflict'
    ' ++ "\\t" ++ description.first_line()'
)
BOOKMARK_NAMES_TEMPLATE = 'bookmarks.map(|b| b.name()).join("\\n") ++ "\\n"'
OP_TEMPLATE = 'id.short(12) ++ "\\t" ++ self.workspace_name()'

EXIT_OK = 0
EXIT_SETUP = 1
EXIT_NOT_JJ = 2
EXIT_DECISION = 3

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


def git_ignores(root: Path, relative: str) -> bool:
    """Report whether git ignores `relative` under `root`; False when git is unavailable."""
    if shutil.which("git") is None:
        return False
    proc = subprocess.run(  # noqa: S603 - fixed argument list
        ["git", "check-ignore", "-q", relative],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return proc.returncode == 0


@dataclass
class Check:
    name: str
    status: str  # pass, warn, fail
    detail: str


@dataclass
class Report:
    status: str = "ok"  # ok, setup-required, not-a-jj-repo, decision-required
    jj_version: str | None = None
    root: str | None = None
    colocated: bool | None = None
    workspace: str | None = None
    teach: bool = False
    agent_config: str | None = None
    op_id: str | None = None
    base: str | None = None
    working_copy: dict[str, object] = field(default_factory=dict)
    bookmarks: list[str] = field(default_factory=list)
    trunk: list[str] = field(default_factory=list)
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, status: str, detail: str) -> None:
        """Record one check result."""
        self.checks.append(Check(name, status, detail))

    @property
    def failed(self) -> bool:
        """True when any check has status fail."""
        return any(c.status == "fail" for c in self.checks)


def parse_version(text: str) -> tuple[int, int, int] | None:
    """Read the version triple out of `jj --version` output such as `jj 0.41.0`."""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3))


def find_teach_flag(root: Path) -> bool:
    """Report whether a project instruction file at the root carries the line `jj: teach`."""
    for name in TEACH_FILES:
        path = root / name
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if any(TEACH_LINE.match(line) for line in text.splitlines()):
            return True
    return False


def resolve_agent_config(explicit: str | None) -> Path:
    """Pick the agent signing config path: flag, then JJ_AGENT_CONFIG, then the default."""
    candidate = explicit or os.environ.get("JJ_AGENT_CONFIG") or str(DEFAULT_AGENT_CONFIG)
    return Path(candidate).expanduser()


def check_agent_config(path: Path) -> tuple[str, str]:
    """Return (status, detail) for the agent signing config file.

    The file must parse as TOML, name a known `signing.backend`, and name a
    `signing.key`. A key written as a path must exist on disk; a key written
    as a key ID (no path separator) is accepted as is.
    """
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "fail", f"agent signing config not found at {path}; see references/setup.md"
    except (OSError, tomllib.TOMLDecodeError) as exc:
        return "fail", f"agent signing config at {path} is unreadable: {exc}"
    signing = data.get("signing")
    if not isinstance(signing, dict):
        return "fail", f"agent signing config at {path} has no [signing] table"
    backend = signing.get("backend")
    if backend not in SIGNING_BACKENDS:
        return (
            "fail",
            f"agent signing config at {path}: signing.backend must be one of: {' '.join(SIGNING_BACKENDS)} (got: {backend!r})",
        )
    key = signing.get("key")
    if not isinstance(key, str) or not key:
        return "fail", f"agent signing config at {path} has no signing.key"
    if "/" in key or key.startswith("~"):
        key_path = Path(key).expanduser()
        if not key_path.exists():
            return "fail", f"agent signing config at {path} names key {key}, which does not exist"
    return "pass", f"agent signing config at {path}: backend {backend}, key {key}"


def config_get(runner: Runner, root: Path, key: str) -> str | None:
    """Return a config value, or None when jj reports it is not set."""
    code, out, _ = runner(["config", "get", key], root)
    if code != 0:
        return None
    return out.strip()


def parse_working_copy(line: str) -> dict[str, object]:
    """Parse the tab-separated template output describing `@`."""
    parts = line.rstrip("\n").split("\t")
    if len(parts) < 5:
        return {}
    change_id, commit_id, empty, conflict, description = parts[:5]
    return {
        "change_id": change_id,
        "commit_id": commit_id,
        "empty": empty == "true",
        "conflict": conflict == "true",
        "description": description,
    }


def names(out: str) -> list[str]:
    """Sorted unique non-empty lines of template output."""
    return sorted({line.strip() for line in out.splitlines() if line.strip()})


def locate_repo(runner: Runner, cwd: Path, report: Report, jj_found: bool) -> Path | None:
    """Record the jj version and repo root; return the root, or None when jj does not apply here."""
    if not jj_found:
        report.status = "not-a-jj-repo"
        report.add("jj-installed", "fail", "jj binary not found on PATH")
        return None

    code, out, err = runner(["--version"], cwd)
    version = parse_version(out) if code == 0 else None
    if version is None:
        report.status = "not-a-jj-repo"
        report.add("jj-installed", "fail", f"could not read jj version: {err.strip() or out.strip()}")
        return None
    report.jj_version = ".".join(str(n) for n in version)
    if version < MIN_VERSION:
        floor = ".".join(str(n) for n in MIN_VERSION)
        report.add("jj-version", "fail", f"jj {report.jj_version} is below the floor {floor}")
    else:
        report.add("jj-version", "pass", f"jj {report.jj_version}")

    code, out, err = runner(["root"], cwd)
    if code != 0:
        report.status = "not-a-jj-repo"
        report.add("jj-repo", "fail", f"not inside a jj repo: {err.strip()}")
        return None
    root = Path(out.strip())
    report.root = str(root)
    report.add("jj-repo", "pass", f"repo root {root}")
    return root


def check_setup(runner: Runner, root: Path, agent_config: Path, report: Report) -> None:
    """Record colocation, identity, signing config, and the config items the setup checklist asks for."""
    report.colocated = (root / ".git").exists()
    if report.colocated:
        report.add("colocated", "pass", ".git present next to .jj")
    else:
        report.add(
            "colocated",
            "warn",
            "no .git here: a secondary workspace or a non-colocated repo; git tooling needs the detour in references/workspaces.md",
        )

    for key in ("user.name", "user.email"):
        value = config_get(runner, root, key)
        if value:
            report.add(key, "pass", f"{key} = {value}")
        else:
            report.add(key, "fail", f"{key} is not set; see references/setup.md")

    status, detail = check_agent_config(agent_config)
    report.agent_config = str(agent_config)
    report.add("agent-signing-config", status, detail)

    immutable = config_get(runner, root, 'revset-aliases."immutable_heads()"') or ""
    if REMOTE_BOOKMARKS_ALIAS.search(immutable):
        report.add("immutable-remote-bookmarks", "pass", f"immutable_heads() = {immutable}")
    else:
        report.add(
            "immutable-remote-bookmarks",
            "warn",
            "immutable_heads() does not include remote_bookmarks(); pushed branches stay rewritable",
        )

    markers = config_get(runner, root, "ui.conflict-marker-style") or "diff"
    if markers == "git":
        report.add("conflict-markers", "pass", "ui.conflict-marker-style = git")
    else:
        report.add(
            "conflict-markers",
            "warn",
            f"ui.conflict-marker-style = {markers}; pass --config ui.conflict-marker-style=git on rebase and new",
        )

    if report.colocated and (root / WORKTREES_DIR).exists():
        if git_ignores(root, WORKTREES_DIR):
            report.add("worktrees-ignored", "pass", f"{WORKTREES_DIR}/ is git-ignored")
        else:
            report.add(
                "worktrees-ignored",
                "warn",
                f"{WORKTREES_DIR}/ exists and is not git-ignored; its files would reach the hook run and the next snapshot",
            )


def inspect_working_copy(runner: Runner, root: Path, report: Report) -> bool:
    """Record the state of `@` and the base of the agent's stack; return True when `@` holds undescribed edits."""
    code, out, _ = runner(["log", "-r", "@", "--no-graph", "-T", WORKING_COPY_TEMPLATE], root)
    if code != 0:
        return False
    report.working_copy = parse_working_copy(out)
    wc = report.working_copy
    if not wc:
        return False

    undescribed_edits = not wc["empty"] and not wc["description"]
    if undescribed_edits:
        code, out, _ = runner(["diff", "-r", "@", "--name-only"], root)
        files = [line for line in out.splitlines() if line] if code == 0 else []
        wc["files"] = files
        report.add(
            "working-copy",
            "warn",
            f"@ holds {len(files)} changed file(s) and no description; the human decides how to close them",
        )
    else:
        state = "empty" if wc["empty"] else "has content"
        report.add(
            "working-copy", "pass", f"@ {wc['change_id']} {state}, description: {wc['description'] or '(none)'}"
        )

    if wc["empty"] and not wc["description"]:
        code, out, _ = runner(["log", "-r", "@-", "--no-graph", "-T", "change_id.short()"], root)
        report.base = out.strip() if code == 0 and out.strip() else None
    else:
        report.base = str(wc["change_id"])
    return undescribed_edits


def inspect_position(runner: Runner, root: Path, report: Report) -> None:
    """Record the nearest bookmarks, the trunk, the current workspace, and the latest operation."""
    code, out, _ = runner(["log", "-r", "heads(::@ & bookmarks())", "--no-graph", "-T", BOOKMARK_NAMES_TEMPLATE], root)
    if code == 0:
        report.bookmarks = names(out)
    code, out, _ = runner(["log", "-r", "trunk()", "--no-graph", "-T", BOOKMARK_NAMES_TEMPLATE], root)
    if code == 0:
        report.trunk = names(out)
    if not report.trunk:
        report.add("trunk", "warn", "no trunk bookmark; trunk() resolves to root(), so trunk()..@ spans all history")

    code, out, _ = runner(["op", "log", "-n", "1", "--no-graph", "-T", OP_TEMPLATE], root)
    if code == 0 and out.strip():
        op_id, _, workspace = out.strip().partition("\t")
        report.op_id = op_id
        report.workspace = workspace.rstrip("@") or None


def collect(runner: Runner, cwd: Path, agent_config: Path, jj_found: bool = True) -> Report:
    """Run every check and assemble the report."""
    report = Report()
    root = locate_repo(runner, cwd, report, jj_found)
    if root is None:
        return report

    check_setup(runner, root, agent_config, report)
    report.teach = find_teach_flag(root)
    undescribed_edits = inspect_working_copy(runner, root, report)
    inspect_position(runner, root, report)

    if report.failed:
        report.status = "setup-required"
    elif undescribed_edits:
        report.status = "decision-required"
    return report


def exit_code(report: Report) -> int:
    """Map the report status to the process exit code."""
    return {
        "ok": EXIT_OK,
        "setup-required": EXIT_SETUP,
        "not-a-jj-repo": EXIT_NOT_JJ,
        "decision-required": EXIT_DECISION,
    }[report.status]


def render_text(report: Report) -> str:
    """One-screen digest for a human."""
    lines = [f"status: {report.status}"]
    if report.jj_version:
        lines.append(f"jj: {report.jj_version}  root: {report.root}  colocated: {report.colocated}")
    lines.append(f"workspace: {report.workspace}  teach: {report.teach}  op: {report.op_id}  base: {report.base}")
    if report.working_copy:
        wc = report.working_copy
        lines.append(f"@: {wc.get('change_id')} {wc.get('description') or '(no description)'} empty={wc.get('empty')}")
        if wc.get("files"):
            lines.append("  files: " + " ".join(str(f) for f in wc["files"]))
    lines.append(f"bookmarks: {' '.join(report.bookmarks) or '-'}  trunk: {' '.join(report.trunk) or '-'}")
    lines.extend(f"[{c.status}] {c.name}: {c.detail}" for c in report.checks)
    return "\n".join(lines)


def main(argv: list[str] | None = None, runner: Runner = run_jj, jj_found: bool | None = None) -> int:
    """Parse arguments, run the checks, print the report, and return the exit code."""
    parser = argparse.ArgumentParser(description="Orient checks for the jj skill.")
    parser.add_argument("--repo", default=".", help="directory inside the repo (default: current directory)")
    parser.add_argument(
        "--agent-config",
        default=None,
        help="agent signing config path (default: $JJ_AGENT_CONFIG or ~/.config/jj/agent.toml)",
    )
    parser.add_argument("--format", choices=("json", "text"), default="json")
    args = parser.parse_args(argv)

    found = shutil.which("jj") is not None if jj_found is None else jj_found
    report = collect(runner, Path(args.repo), resolve_agent_config(args.agent_config), jj_found=found)

    if args.format == "json":
        print(json.dumps(asdict(report), indent=2))
    else:
        print(render_text(report))
    for check in report.checks:
        if check.status != "pass":
            print(f"{check.status}: {check.name}: {check.detail}", file=sys.stderr)
    return exit_code(report)


if __name__ == "__main__":
    sys.exit(main())
