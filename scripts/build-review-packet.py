#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Pre-bake a review packet (diff + metadata + source-of-truth) for reviewers.

A reviewer — human or subagent — handed only "go review the branch" tends to
issue many exploratory git commands to resolve the base ref and assemble the
diff. That is slow and burns tokens. This script does the deterministic git
work once and emits a single packet file that reviewers read by path, so they
do not re-derive scope or re-run git.

It is consumed (via a symlink under each skill's scripts/) by the code-review
and simplify review paths. The canonical copy lives at the repo root scripts/
because it is shared across skill families; `npx skills` dereferences the
symlink into an independent copy at install time.

Source-of-truth: a reviewer given only a diff will confidently grade it against
a spec it invents. Pass the intent/spec via --intent / --include so the packet
carries what the change is judged against. When neither is supplied the packet
says so loudly and the JSON sets has_source_of_truth=false, so the calling
skill can refuse to dispatch a spec-compliance reviewer on an invented spec.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
import subprocess
import sys
import tempfile

DEFAULT_MAX_DIFF_BYTES = 400_000


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a git subcommand in `repo` and capture its output."""
    # Args are git subcommands chosen by this script, not untrusted input.
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
    )


def is_git_repo(repo: Path) -> bool:
    """Return True if `repo` is inside a git work tree."""
    return git(repo, "rev-parse", "--is-inside-work-tree", check=False).returncode == 0


def resolve_base(repo: Path, explicit: str | None) -> str | None:
    """Resolve the comparison base: explicit, else origin/HEAD, else main/master."""
    if explicit:
        return explicit
    head_ref = git(repo, "rev-parse", "--abbrev-ref", "origin/HEAD", check=False)
    if head_ref.returncode == 0 and head_ref.stdout.strip():
        return head_ref.stdout.strip().removeprefix("origin/")
    for candidate in ("main", "master"):
        if git(repo, "rev-parse", "--verify", "--quiet", candidate, check=False).returncode == 0:
            return candidate
    return None


def detect_scope(repo: Path, args: argparse.Namespace) -> str:
    """Pick the diff scope. Explicit flags win; --auto falls back staged > branch > worktree."""
    if args.staged:
        return "staged"
    if args.base:
        return "branch"
    if args.worktree:
        return "worktree"
    # --auto (default)
    if git(repo, "diff", "--cached", "--quiet", check=False).returncode != 0:
        return "staged"
    base = resolve_base(repo, None)
    if base:
        merge_base = git(repo, "merge-base", base, "HEAD", check=False)
        head = git(repo, "rev-parse", "HEAD", check=False).stdout.strip()
        if merge_base.returncode == 0 and merge_base.stdout.strip() and merge_base.stdout.strip() != head:
            return "branch"
    if git(repo, "diff", "--quiet", "HEAD", check=False).returncode != 0:
        return "worktree"
    return "empty"


def diff_range(repo: Path, scope: str, base: str | None) -> tuple[list[str], dict[str, str]]:
    """Return the git diff argument list for the scope, plus metadata about the range."""
    if scope == "staged":
        return ["diff", "--cached"], {"scope": "staged", "range": "index vs HEAD"}
    if scope == "worktree":
        return ["diff", "HEAD"], {"scope": "worktree", "range": "working tree vs HEAD"}
    if scope == "branch":
        merge_base = git(repo, "merge-base", base, "HEAD").stdout.strip()
        return (
            ["diff", f"{merge_base}...HEAD"],
            {"scope": "branch", "base": base or "", "merge_base": merge_base, "range": f"{base} ({merge_base})...HEAD"},
        )
    return ["diff", "--cached"], {"scope": "empty", "range": "no changes detected"}


def render_source_of_truth(intent: str | None, includes: list[Path]) -> tuple[str, bool]:
    """Render the source-of-truth section. Returns (markdown, has_source_of_truth).

    has_source_of_truth is true only when real content was captured — a stated
    intent, or at least one include that actually read. Includes that are
    missing or unreadable are noted but do not count, so a packet whose only
    "spec" failed to load is still flagged false.
    """
    warning = (
        "> **NO SOURCE OF TRUTH PROVIDED.**\n"
        "> This packet contains only a diff. A reviewer judging spec compliance\n"
        "> from a bare diff will silently invent a spec and grade against it.\n"
        "> Do not run a spec-compliance pass on this packet. Re-run with\n"
        "> `--intent` and/or `--include <spec/plan/PR-description>`."
    )

    parts: list[str] = []
    has = bool(intent and intent.strip())
    if intent and intent.strip():
        parts.append("### Stated intent\n\n" + intent.strip())
    for path in includes:
        if not path.exists():
            parts.append(f"### Missing include: `{path}`\n\n> File not found at packet build time.")
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            parts.append(f"### Unreadable include: `{path}`\n\n> {exc}")
            continue
        parts.append(f"### Included: `{path}`\n\n```\n{body}\n```")
        has = True

    if not has:
        return (warning + ("\n\n" + "\n\n".join(parts) if parts else "")), False
    return "\n\n".join(parts), True


def build_packet(args: argparse.Namespace) -> dict[str, object]:
    """Resolve scope, write the packet file, and return its summary metadata."""
    repo = Path(args.repo).resolve()
    if not is_git_repo(repo):
        raise SystemExit(json.dumps({"error": f"not a git repository: {repo}"}))

    base = resolve_base(repo, args.base) if (args.base or args.auto_needs_base()) else None
    scope = detect_scope(repo, args)
    if scope == "branch" and base is None:
        raise SystemExit(json.dumps({"error": "branch scope requested but no base ref could be resolved"}))

    args_list, range_meta = diff_range(repo, scope, base)
    name_status = git(repo, *args_list, "--name-status").stdout.strip()
    diff = git(repo, *args_list, "--no-color").stdout

    truncated = False
    if len(diff.encode("utf-8")) > args.max_diff_bytes:
        diff = diff.encode("utf-8")[: args.max_diff_bytes].decode("utf-8", errors="ignore")
        truncated = True

    changed_files = [line for line in name_status.splitlines() if line.strip()]
    head = git(repo, "rev-parse", "HEAD", check=False).stdout.strip()
    sot_md, has_sot = render_source_of_truth(args.intent, [Path(p) for p in args.include])
    generated = _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds")

    meta_lines = [
        f"- scope: {range_meta['scope']}",
        f"- range: {range_meta['range']}",
        f"- head: {head or '(unknown)'}",
        f"- changed files: {len(changed_files)}",
        f"- generated (UTC): {generated}",
    ]
    if truncated:
        meta_lines.append(f"- **diff truncated** to {args.max_diff_bytes} bytes; review in-repo for the full diff")

    packet = (
        "# Review Packet\n\n"
        "## Metadata\n\n" + "\n".join(meta_lines) + "\n\n"
        "## Source of truth\n\n" + sot_md + "\n\n"
        "## Changed files (name-status)\n\n"
        + (f"```\n{name_status}\n```" if changed_files else "_No changes in scope._")
        + "\n\n## Diff\n\n"
        + (f"```diff\n{diff}\n```" if diff.strip() else "_Empty diff._")
        + "\n"
    )

    out_path = Path(args.out) if args.out else Path(tempfile.gettempdir()) / f"review-packet-{(head or 'work')[:12]}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(packet, encoding="utf-8")

    return {
        "packet_path": str(out_path),
        "scope": range_meta["scope"],
        "base": range_meta.get("base", ""),
        "head": head,
        "changed_files": len(changed_files),
        "has_source_of_truth": has_sot,
        "diff_truncated": truncated,
        "bytes": out_path.stat().st_size,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments into a namespace consumed by build_packet."""
    parser = argparse.ArgumentParser(description="Build a review packet for reviewers/subagents.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--staged", action="store_true", help="review staged changes (index vs HEAD)")
    scope.add_argument("--worktree", action="store_true", help="review all uncommitted changes (working tree vs HEAD)")
    scope.add_argument("--base", metavar="REF", help="review this branch against base REF (merge-base...HEAD)")
    parser.add_argument("--include", action="append", default=[], metavar="PATH",
                        help="inline a source-of-truth file (spec, plan, PR description); repeatable")
    parser.add_argument("--intent", metavar="TEXT", help="short statement of what the change is meant to do")
    parser.add_argument("--out", metavar="PATH", help="packet output path (default: a file under TMPDIR)")
    parser.add_argument("--repo", default=".", metavar="DIR", help="repository directory (default: cwd)")
    parser.add_argument("--max-diff-bytes", type=int, default=DEFAULT_MAX_DIFF_BYTES, dest="max_diff_bytes",
                        help=f"truncate the diff past this many bytes (default: {DEFAULT_MAX_DIFF_BYTES})")
    ns = parser.parse_args(argv)
    ns.auto_needs_base = lambda: not (ns.staged or ns.worktree)
    return ns


def main(argv: list[str]) -> int:
    """Build the packet and print its summary JSON to stdout."""
    args = parse_args(argv)
    result = build_packet(args)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
