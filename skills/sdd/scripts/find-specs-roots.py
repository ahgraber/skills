#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Resolve SPECS_ROOT candidates for the sdd skill.

A `SPECS_ROOT` is a directory whose direct children conform to the SDD layout: `specs/`, `changes/`, and `schemas/` (with optional `.sdd/`).
The conventional location is a hidden `.specs/` at a project root; in a monorepo, each package may have its own `<package>/.specs/`.

Emits a single JSON object describing the workspace anchor, any explicit user
path, discovered `.specs/` candidates (with pointer-file analysis), and
`specs/` fallback candidates. The caller (the sdd skill) uses this data to
drive user dialogue and select a final `SPECS_ROOT`. This script makes no
interactive decisions.

Usage:
    find-specs-roots.py [--explicit PATH] [--workspace PATH]
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Literal

EXCLUDE_DIRS = {
    ".git",
    ".nox",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "site-packages",
    "target",
    "vendor",
    "venv",
}
SPECS_FALLBACK_MAX_DEPTH = 4


@dataclass
class TargetInfo:
    raw: str
    comment: str | None
    resolved: str
    exists: bool
    is_dir: bool = False
    outside_workspace: bool = False


@dataclass
class PointerInfo:
    malformed: bool = False
    malformed_reason: Literal["unreadable", "empty"] | None = None
    malformed_detail: str | None = None
    targets: list[TargetInfo] = field(default_factory=list)


@dataclass
class DotSpecsCandidate:
    path: str
    pointer: PointerInfo | None = None


@dataclass
class SpecsFallbackCandidate:
    path: str  # the specs/ directory
    parent: str  # parent of specs/ — the SDD-layout default for SPECS_ROOT


@dataclass
class ExplicitPath:
    raw: str
    resolved: str
    exists: bool
    outside_workspace: bool


@dataclass
class Result:
    anchor_path: str
    anchor_source: str  # "git" or "cwd"
    explicit: ExplicitPath | None = None
    dot_specs_candidates: list[DotSpecsCandidate] = field(default_factory=list)
    specs_fallback_candidates: list[SpecsFallbackCandidate] = field(default_factory=list)
    fallback_used: bool = False


def find_anchor(override: Path | None) -> tuple[Path, str]:
    """Return the workspace anchor path and its source ("override", "git", or "cwd")."""
    if override is not None:
        return override.resolve(), "override"
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        proc = None
    if proc is not None and proc.returncode == 0 and proc.stdout.strip():
        return Path(proc.stdout.strip()).resolve(), "git"
    return Path.cwd().resolve(), "cwd"


def is_inside(child: Path, ancestor: Path) -> bool:
    """Return True if `child` is `ancestor` or lives beneath it."""
    try:
        child.resolve().relative_to(ancestor.resolve())
    except ValueError:
        return False
    else:
        return True


def walk_for_dirs(
    anchor: Path,
    name: str,
    max_depth: int | None,
) -> list[Path]:
    """Find directories named `name` under anchor, skipping excluded subdirs.

    `max_depth` counts directories below the anchor: depth 1 = direct children.
    None means unlimited.
    """
    results: list[Path] = []
    anchor_resolved = anchor.resolve()
    for root, dirs, _files in os.walk(anchor_resolved, followlinks=False):
        root_path = Path(root).resolve()
        try:
            rel_depth = len(root_path.relative_to(anchor_resolved).parts)
        except ValueError:
            # Symlink escaped the anchor; skip
            dirs[:] = []
            continue
        # Prune excluded directories before recursion
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        # Capture matches at the current level
        for d in dirs:
            if d == name:
                cand = (root_path / d).resolve()
                if is_inside(cand, anchor_resolved):
                    results.append(cand)
        # Enforce max depth: at this level we already collected matches one level
        # below; if descending further would exceed max_depth, stop.
        if max_depth is not None and rel_depth + 1 >= max_depth:
            dirs[:] = []
    return sorted(set(results))


def parse_pointer_file(
    path: Path,
) -> tuple[list[tuple[str, str | None]], Literal["unreadable", "empty"] | None, str | None]:
    """Return (entries, malformed_reason, malformed_detail).

    entries is a list of (path_str, comment_or_none) pairs. Blank lines and
    lines whose first non-whitespace character is '#' are skipped. Trailing
    ' #' and ' //' comments (space-prefixed) are stripped from each remaining
    line; whichever marker appears earliest wins. The comment text is
    captured separately.
    malformed_reason is 'unreadable' when the file cannot be read or is not
    valid UTF-8, 'empty' when no non-comment lines remain.
    malformed_detail carries the OS error string for 'unreadable'.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [], "unreadable", str(exc)
    entries: list[tuple[str, str | None]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        comment: str | None = None
        matches = [(stripped.find(m), m) for m in (" #", " //")]
        matches = [(i, m) for i, m in matches if i != -1]
        if matches:
            idx, marker = min(matches)
            comment = stripped[idx + len(marker) :].strip() or None
            stripped = stripped[:idx].strip()
        if stripped:
            entries.append((stripped, comment))
    if not entries:
        return [], "empty", None
    return entries, None, None


def resolve_pointer_target(raw: str, marker_dir: Path) -> Path:
    """Resolve a pointer-file target string, treating relative paths as relative to `marker_dir`."""
    expanded = os.path.expanduser(raw)
    p = Path(expanded)
    if p.is_absolute():
        return p.resolve()
    return (marker_dir / p).resolve()


def analyze_pointer(marker_dir: Path, anchor: Path) -> PointerInfo | None:
    """Inspect `marker_dir/SPECS_ROOT` and return its parsed state, or None when the file is absent."""
    pointer_file = marker_dir / "SPECS_ROOT"
    if not pointer_file.is_file():
        return None
    entries, malformed_reason, malformed_detail = parse_pointer_file(pointer_file)
    if malformed_reason is not None:
        return PointerInfo(
            malformed=True,
            malformed_reason=malformed_reason,
            malformed_detail=malformed_detail,
        )
    targets: list[TargetInfo] = []
    for raw, comment in entries:
        target_path = resolve_pointer_target(raw, marker_dir)
        t = TargetInfo(raw=raw, comment=comment, resolved=str(target_path), exists=target_path.exists())
        if t.exists:
            t.is_dir = target_path.is_dir()
            t.outside_workspace = not is_inside(target_path, anchor)
        targets.append(t)
    return PointerInfo(targets=targets)


def analyze_explicit(raw: str, anchor: Path) -> ExplicitPath:
    """Resolve a user-provided explicit path and report its existence and workspace containment."""
    expanded = os.path.expanduser(raw)
    p = Path(expanded)
    p = p.resolve() if p.is_absolute() else (Path.cwd() / p).resolve()
    return ExplicitPath(
        raw=raw,
        resolved=str(p),
        exists=p.exists(),
        outside_workspace=not is_inside(p, anchor),
    )


def main() -> int:
    """Parse CLI args, run discovery, and print the result JSON to stdout."""
    parser = argparse.ArgumentParser(description="Resolve SPECS_ROOT candidates for the sdd skill.")
    parser.add_argument("--explicit", help="User-specified explicit path (overrides discovery).")
    parser.add_argument(
        "--workspace",
        help="Override the workspace anchor (default: git repo root, else cwd).",
    )
    args = parser.parse_args()

    workspace_override = Path(args.workspace) if args.workspace else None
    anchor, anchor_source = find_anchor(workspace_override)
    result = Result(anchor_path=str(anchor), anchor_source=anchor_source)

    if args.explicit:
        result.explicit = analyze_explicit(args.explicit, anchor)
        # When explicit is given, do not discover or follow pointers.
        print(json.dumps(asdict(result), indent=2))
        return 0

    dot_specs_dirs = walk_for_dirs(anchor, ".specs", max_depth=None)
    for marker_dir in dot_specs_dirs:
        cand = DotSpecsCandidate(path=str(marker_dir))
        cand.pointer = analyze_pointer(marker_dir, anchor)
        result.dot_specs_candidates.append(cand)

    if not result.dot_specs_candidates:
        result.fallback_used = True
        specs_dirs = walk_for_dirs(anchor, "specs", max_depth=SPECS_FALLBACK_MAX_DEPTH)
        for d in specs_dirs:
            result.specs_fallback_candidates.append(SpecsFallbackCandidate(path=str(d), parent=str(d.parent)))

    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
