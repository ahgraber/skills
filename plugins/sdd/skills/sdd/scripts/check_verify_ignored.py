#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = []
# ///
"""Report whether git ignores sdd-verify's `.verify/` run directories.

`sdd-verify` writes one run directory per verification under each change's
`.verify/`. Whether those runs are committed is the user's choice, recorded as
one ignore rule in `<specs-root>/.gitignore` rather than a file in every
`.verify/`. The agent runs this script at the start of verification: when it
reports `first_run`, the agent asks the user once and, on a yes, re-runs it
with `--add`.

Prints JSON: `ignored`, `rule` (the matching ignore rule, or null),
`verify_dirs` (existing `.verify/` directories under the specs root), and
`first_run` (not ignored and no `.verify/` directory exists yet).
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

RULE = ".verify/"


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git subcommand in `repo` and capture its output."""
    # Args are git subcommands chosen by this script, not untrusted input.
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)  # noqa: S603


def matching_rule(specs_root: Path) -> str | None:
    """Return the ignore rule that covers a `.verify/` run directory, or None."""
    probe = specs_root / "changes" / "probe-change" / ".verify" / "probe-run" / "report.md"
    result = git(specs_root, "check-ignore", "-v", "--no-index", str(probe))
    if result.returncode != 0:
        return None
    source = result.stdout.split("\t", 1)[0].strip()
    return source or None


def status(specs_root: Path) -> dict[str, object]:
    """Summarize whether `.verify/` is ignored and whether any run exists yet."""
    rule = matching_rule(specs_root)
    dirs = sorted(str(p) for p in specs_root.rglob(".verify") if p.is_dir())
    return {"ignored": rule is not None, "rule": rule, "verify_dirs": dirs, "first_run": rule is None and not dirs}


def add_rule(specs_root: Path) -> None:
    """Append the `.verify/` rule to `<specs-root>/.gitignore`, creating the file if needed."""
    gitignore = specs_root / ".gitignore"
    text = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if RULE in text.splitlines():
        return
    prefix = "" if not text or text.endswith("\n") else "\n"
    gitignore.write_text(f"{text}{prefix}{RULE}\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    """Print the ignore status, adding the rule first when `--add` is given."""
    parser = argparse.ArgumentParser(description="Report whether git ignores .verify/ run directories.")
    parser.add_argument("specs_root", help="the SDD specs root, for example .specs")
    parser.add_argument("--add", action="store_true", help="add the .verify/ rule to <specs-root>/.gitignore")
    args = parser.parse_args(argv)
    specs_root = Path(args.specs_root).resolve()
    if git(specs_root, "rev-parse", "--is-inside-work-tree").returncode != 0:
        print(json.dumps({"error": f"not inside a git work tree: {specs_root}"}))
        return 2
    if args.add and matching_rule(specs_root) is None:
        add_rule(specs_root)
    print(json.dumps(status(specs_root), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
