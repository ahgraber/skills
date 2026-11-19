#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
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

Index: the JSON output gives the line range of each packet section and of each
file's hunks, so a caller can point a reader at the part it needs instead of
the whole packet. `packet_tokens` estimates the packet's size (bytes / 4).
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

DEFAULT_MAX_DIFF_BYTES = 400_000

OUTPUT_DIRS = (".review", "._scratch", ".scratch")


def git(repo: Path, *args: str, check: bool = True, stdin: str | None = None) -> subprocess.CompletedProcess[str]:
    """Run a git subcommand in `repo` and capture its output."""
    # Args are git subcommands chosen by this script, not untrusted input.
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), *args],
        capture_output=True,
        text=True,
        check=check,
        input=stdin,
    )


# The whole repository, without the `.verify/` directory of an SDD change, active
# or archived: `sdd-verify` keeps its run logs and reports there, and they are not
# part of the change under review. A `.verify/` directory elsewhere, such as a
# formal-verification effort's records, stays in. Both patterns are relative to
# the repository root, so `--repo` may name a subdirectory.
PATHSPEC = (":/", ":(top,exclude,glob)**/changes/**/.verify/**")


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


def default_out_dir(repo: Path) -> Path:
    """Return the first existing OUTPUT_DIRS entry at the repo root, else TMPDIR."""
    toplevel = git(repo, "rev-parse", "--show-toplevel", check=False).stdout.strip()
    root = Path(toplevel) if toplevel else repo
    for name in OUTPUT_DIRS:
        if (root / name).is_dir():
            return root / name
    return Path(tempfile.gettempdir())


def current_branch(repo: Path) -> str:
    """Return the checked-out branch name, or "" on a detached HEAD."""
    name = git(repo, "rev-parse", "--abbrev-ref", "HEAD", check=False).stdout.strip()
    return "" if name in ("", "HEAD") else name


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text).strip("-") or "none"


def detect_scope(repo: Path, args: argparse.Namespace) -> str:
    """Pick the diff scope. Explicit flags win; --auto falls back staged > branch > worktree."""
    if args.staged:
        return "staged"
    if args.base:
        return "branch"
    if args.worktree:
        return "worktree"
    # --auto (default)
    if git(repo, "diff", "--cached", "--quiet", "--", *PATHSPEC, check=False).returncode != 0:
        return "staged"
    base = resolve_base(repo, None)
    if base:
        merge_base = git(repo, "merge-base", base, "HEAD", check=False)
        head = git(repo, "rev-parse", "HEAD", check=False).stdout.strip()
        if merge_base.returncode == 0 and merge_base.stdout.strip() and merge_base.stdout.strip() != head:
            return "branch"
    if git(repo, "diff", "--quiet", "HEAD", "--", *PATHSPEC, check=False).returncode != 0 or untracked_files(repo):
        return "worktree"
    return "empty"


def untracked_files(repo: Path) -> list[str]:
    """Return the files git does not track and does not ignore, relative to the repository root."""
    out = git(repo, "ls-files", "-z", "--others", "--exclude-standard", "--full-name", "--", *PATHSPEC).stdout
    return [p for p in out.split("\0") if p]


def untracked_diff(repo: Path) -> tuple[str, str]:
    """Return the name-status lines and the diff that show each untracked file as a new file."""
    paths = untracked_files(repo)
    root = Path(git(repo, "rev-parse", "--show-toplevel").stdout.strip())
    name_status = "".join(f"A\t{p}\n" for p in paths)
    # --no-index exits 1 when the files differ, which they always do here.
    diff = "".join(
        git(root, "diff", "--no-index", "--no-color", "--", "/dev/null", p, check=False).stdout for p in paths
    )
    return name_status, diff


def content_ids(repo: Path, scope: str, paths: list[str]) -> dict[str, str]:
    """Return each changed file's blob id in the content the scope reviews; a file absent there maps to "".

    The staged scope reviews the index, the branch scope ``HEAD``, and the
    worktree scope the files on disk, where a symlink's id is that of its link
    text, as git stores it. ``review_state.py`` compares these ids
    with the content at the time it starts the review and dispatches each role.
    """
    ids = dict.fromkeys(paths, "")
    if not paths:
        return ids
    if scope in ("staged", "branch"):
        command = ("ls-files", "-s", "-z") if scope == "staged" else ("ls-tree", "-r", "-z", "HEAD")
        field = 1 if scope == "staged" else 2
        for line in git(repo, *command, "--", *paths, check=False).stdout.split("\0"):
            if "\t" in line:
                meta, path = line.split("\t", 1)
                if path in ids:
                    ids[path] = meta.split()[field]
        return ids
    return {path: _disk_id(repo, path) for path in paths}


def _disk_id(repo: Path, path: str) -> str:
    """Return the blob id git would store for `path` on disk, or "" when it is absent."""
    if (repo / path).is_symlink():
        return git(repo, "hash-object", "--stdin", stdin=str((repo / path).readlink())).stdout.strip()
    if (repo / path).is_file():
        return git(repo, "hash-object", "--", path).stdout.strip()
    return ""


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
            {
                "scope": "branch",
                "base": base or "",
                "merge_base": merge_base,
                "range": f"{base} ({merge_base})...HEAD",
            },
        )
    return ["diff", "--cached"], {"scope": "empty", "range": "no changes detected"}


def render_source_of_truth(intent: str | None, includes: list[Path]) -> tuple[str, bool, list[str]]:
    """Render the source-of-truth section. Returns (markdown, has_source_of_truth, missing includes).

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
    missing: list[str] = []
    has = bool(intent and intent.strip())
    if intent and intent.strip():
        parts.append("### Stated intent\n\n" + intent.strip())
    for path in includes:
        if not path.exists():
            parts.append(f"### Missing include: `{path}`\n\n> File not found at packet build time.")
            missing.append(str(path))
            continue
        try:
            body = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            parts.append(f"### Unreadable include: `{path}`\n\n> {exc}")
            missing.append(str(path))
            continue
        parts.append(f"### Included: `{path}`\n\n```\n{body}\n```")
        has = True

    if not has:
        return (warning + ("\n\n" + "\n\n".join(parts) if parts else "")), False, missing
    return "\n\n".join(parts), True, missing


PACKET_SECTIONS = ("Metadata", "Changed files (name-status)", "Diff", "Source of truth")


def index_packet(packet: str) -> dict[str, dict[str, list[int]]]:
    """Return 1-based, inclusive line ranges for each packet section and each file's hunks in the diff."""
    lines = packet.split("\n")
    sections = _section_ranges(lines)
    diff = sections.get("Diff")
    files = _file_ranges(lines, diff[0], diff[1]) if diff else {}
    return {"sections": sections, "files": files}


def _section_ranges(lines: list[str]) -> dict[str, list[int]]:
    """Find the packet's own headings, in their fixed order; headings inside included files are content."""
    starts: list[tuple[int, str]] = []
    position = 0
    for name in PACKET_SECTIONS:
        heading = f"## {name}"
        found = next((n for n in range(position, len(lines)) if lines[n] == heading), None)
        if found is not None:
            starts.append((found + 1, name))
            position = found + 1
    sections: dict[str, list[int]] = {}
    for i, (start, name) in enumerate(starts):
        end = starts[i + 1][0] - 1 if i + 1 < len(starts) else len(lines)
        while end > start and not lines[end - 1].strip():
            end -= 1
        sections[name] = [start, end]
    return sections


_C_ESCAPES = {"a": 7, "b": 8, "t": 9, "n": 10, "v": 11, "f": 12, "r": 13, '"': 34, "\\": 92}


def _unquote_c(text: str, start: int) -> tuple[str, int]:
    """Decode git's C-style quoted path starting at the quote at `start`; return it and the index after."""
    out = bytearray()
    i = start + 1
    while i < len(text) and text[i] != '"':
        char = text[i]
        if char == "\\" and i + 1 < len(text):
            following = text[i + 1]
            if following in "01234567":
                out.append(int(text[i + 1 : i + 4], 8))
                i += 4
                continue
            out.append(_C_ESCAPES.get(following, ord(following)))
            i += 2
            continue
        out.extend(char.encode("utf-8"))
        i += 1
    return out.decode("utf-8", errors="replace"), i + 1


def diff_header_path(rest: str) -> str:
    """Return the new-side path from the part of a `diff --git` header after `diff --git `.

    Git quotes a path that holds a quote, a backslash, a control character, or
    (by default) a non-ASCII byte. An unquoted header is ambiguous when a path
    holds " b/", so the equal-halves form is tried first.
    """
    if rest.startswith('"'):
        _, after = _unquote_c(rest, 0)
        rest_b = rest[after:].lstrip(" ")
    else:
        size = (len(rest) - 5) // 2
        if rest == f"a/{rest[2 : 2 + size]} b/{rest[2 : 2 + size]}":
            return rest[2 : 2 + size]
        quoted = rest.find(' "b/')
        rest_b = rest[quoted + 1 :] if quoted != -1 else rest[rest.rfind(" b/") + 1 :]
    if rest_b.startswith('"'):
        path, _ = _unquote_c(rest_b, 0)
    else:
        path = rest_b
    return path.removeprefix("b/")


def _file_ranges(lines: list[str], first: int, last: int) -> dict[str, list[int]]:
    """Find each file's hunks between lines `first` and `last` of the packet."""
    files: dict[str, list[int]] = {}
    current: str | None = None
    for number in range(first, last + 1):
        line = lines[number - 1]
        if line.startswith("diff --git "):
            current = diff_header_path(line[len("diff --git ") :])
            files[current] = [number, number]
        elif line == "```":
            current = None
        elif current is not None and line.strip():
            files[current][1] = number
    return files


def build_packet(args: argparse.Namespace) -> dict[str, object]:
    """Resolve scope, write the packet file, and return its summary metadata."""
    repo = Path(args.repo).resolve()
    if not is_git_repo(repo):
        raise SystemExit(
            json.dumps({"error": f"not a git repository: {repo}; pass --repo <a directory inside the repository>"})
        )

    base = resolve_base(repo, args.base) if (args.base or args.auto_needs_base()) else None
    scope = detect_scope(repo, args)
    if scope == "branch" and base is None:
        msg = "branch scope requested but no base ref could be resolved; pass --base <the branch this one merges into>"
        raise SystemExit(json.dumps({"error": msg}))

    args_list, range_meta = diff_range(repo, scope, base)
    name_status = git(repo, *args_list, "--name-status", "--", *PATHSPEC).stdout
    diff = git(repo, *args_list, "--no-color", "--", *PATHSPEC).stdout
    if scope == "worktree":
        new_status, new_diff = untracked_diff(repo)
        name_status, diff = name_status + new_status, diff + new_diff
    name_status = name_status.strip()

    truncated = False
    if len(diff.encode("utf-8")) > args.max_diff_bytes:
        diff = diff.encode("utf-8")[: args.max_diff_bytes].decode("utf-8", errors="ignore")
        truncated = True

    changed_files = [line for line in name_status.splitlines() if line.strip()]
    head = git(repo, "rev-parse", "HEAD", check=False).stdout.strip()
    branch = current_branch(repo)
    sot_md, has_sot, missing_includes = render_source_of_truth(args.intent, [Path(p) for p in args.include])
    generated = _dt.datetime.now(_dt.UTC).isoformat(timespec="seconds")

    meta_lines = [
        f"- scope: {range_meta['scope']}",
        f"- range: {range_meta['range']}",
        f"- branch: {branch or '(detached)'}",
        f"- head: {head or '(unknown)'}",
        f"- changed files: {len(changed_files)}",
        f"- generated (UTC): {generated}",
    ]
    if truncated:
        meta_lines.append(f"- **diff truncated** to {args.max_diff_bytes} bytes; review in-repo for the full diff")

    packet = (
        "# Review Packet\n\n"
        "## Metadata\n\n" + "\n".join(meta_lines) + "\n\n"
        "## Changed files (name-status)\n\n"
        + (f"```\n{name_status}\n```" if changed_files else "_No changes in scope._")
        + "\n\n## Diff\n\n"
        + (f"```diff\n{diff}\n```" if diff.strip() else "_Empty diff._")
        + "\n\n## Source of truth\n\n"
        + sot_md
        + "\n"
    )

    out_path = Path(args.out) if args.out else default_out_dir(repo) / f"review-packet-{(head or 'work')[:12]}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(packet, encoding="utf-8")

    index = index_packet(packet)
    return {
        "packet_path": str(out_path),
        "index": index,
        "content": content_ids(repo, range_meta["scope"], list(index["files"])),
        "packet_tokens": len(packet.encode("utf-8")) // 4,
        "scope": range_meta["scope"],
        "base": range_meta.get("base", ""),
        "branch": branch,
        "head": head,
        "changed_files": len(changed_files),
        "has_source_of_truth": has_sot,
        "missing_includes": missing_includes,
        "diff_truncated": truncated,
        "bytes": out_path.stat().st_size,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    """Parse CLI arguments into a namespace consumed by build_packet."""
    parser = argparse.ArgumentParser(description="Build a review packet for reviewers/subagents.")
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--staged", action="store_true", help="review staged changes (index vs HEAD)")
    scope.add_argument(
        "--worktree",
        action="store_true",
        help="review all uncommitted changes (working tree vs HEAD), with untracked files git does not ignore",
    )
    scope.add_argument("--base", metavar="REF", help="review this branch against base REF (merge-base...HEAD)")
    parser.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="PATH",
        help="inline a source-of-truth file (spec, plan, PR description); repeatable",
    )
    parser.add_argument("--intent", metavar="TEXT", help="short statement of what the change is meant to do")
    parser.add_argument(
        "--out",
        metavar="PATH",
        help="packet output path (default: the first existing .review/, ._scratch/, or .scratch/ at the repo root, else TMPDIR)",
    )
    parser.add_argument("--repo", default=".", metavar="DIR", help="repository directory (default: cwd)")
    parser.add_argument(
        "--max-diff-bytes",
        type=int,
        default=DEFAULT_MAX_DIFF_BYTES,
        dest="max_diff_bytes",
        help=f"truncate the diff past this many bytes (default: {DEFAULT_MAX_DIFF_BYTES})",
    )
    ns = parser.parse_args(argv)
    ns.auto_needs_base = lambda: not (ns.staged or ns.worktree)
    return ns


def main(argv: list[str]) -> int:
    """Build the packet and print its summary JSON to stdout."""
    args = parse_args(argv)
    try:
        result = build_packet(args)
    except subprocess.CalledProcessError as exc:
        command = " ".join(exc.cmd[3:]) if isinstance(exc.cmd, list) else str(exc.cmd)
        detail = (exc.stderr or "").strip()
        hint = " Check that --base names an existing ref." if args.base else ""
        print(json.dumps({"error": f"git {command} failed: {detail}.{hint}"}), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
