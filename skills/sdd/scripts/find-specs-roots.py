#!/usr/bin/env -S uv run --script
"""Resolve SPECS_ROOT candidates for the sdd skill.

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
SDD_SHAPE_MARKERS = {"specs", "changes", "schemas"}


@dataclass
class PointerInfo:
    present: bool
    raw_target: str | None = None
    resolved_target: str | None = None
    malformed: bool = False
    malformed_reason: str | None = None
    extra_lines_ignored: bool = False
    target_exists: bool = False
    target_is_dir: bool = False
    target_outside_workspace: bool = False
    target_shape_ok: bool = False
    target_shape_reason: str | None = None


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


def parse_pointer_file(path: Path) -> tuple[str | None, bool, str | None]:
    """Return (raw_target, extra_lines_ignored, malformed_reason)."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, False, f"could not read pointer file: {exc}"
    cleaned: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        cleaned.append(stripped)
    if not cleaned:
        return None, False, "no non-comment line in pointer file"
    return cleaned[0], len(cleaned) > 1, None


def resolve_pointer_target(raw: str, marker_dir: Path) -> Path:
    """Resolve a pointer-file target string, treating relative paths as relative to `marker_dir`."""
    expanded = os.path.expanduser(raw)
    p = Path(expanded)
    if p.is_absolute():
        return p.resolve()
    return (marker_dir / p).resolve()


def analyze_target_shape(target: Path) -> tuple[bool, str | None]:
    """Return (shape_ok, reason_if_not_ok)."""
    if not target.is_dir():
        return False, "target is not a directory"
    try:
        children = list(target.iterdir())
    except OSError as exc:
        return False, f"could not list target: {exc}"
    if not children:
        return True, None  # empty == freshly initialized, OK
    has_marker = any(c.name in SDD_SHAPE_MARKERS and c.is_dir() for c in children)
    if has_marker:
        return True, None
    return False, "target contains no specs/, changes/, or schemas/ subdirectory"


def analyze_pointer(marker_dir: Path, anchor: Path) -> PointerInfo:
    """Inspect `marker_dir/SPECS_ROOT` (if present) and return its parsed/resolved state."""
    pointer_file = marker_dir / "SPECS_ROOT"
    if not pointer_file.is_file():
        return PointerInfo(present=False)
    raw, extra, malformed_reason = parse_pointer_file(pointer_file)
    if malformed_reason is not None or raw is None:
        return PointerInfo(
            present=True,
            malformed=True,
            malformed_reason=malformed_reason,
            extra_lines_ignored=extra,
        )
    target = resolve_pointer_target(raw, marker_dir)
    info = PointerInfo(
        present=True,
        raw_target=raw,
        resolved_target=str(target),
        extra_lines_ignored=extra,
        target_exists=target.exists(),
    )
    if not info.target_exists:
        return info
    info.target_is_dir = target.is_dir()
    info.target_outside_workspace = not is_inside(target, anchor)
    shape_ok, reason = analyze_target_shape(target)
    info.target_shape_ok = shape_ok
    info.target_shape_reason = reason
    return info


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


def to_jsonable(obj):
    """Recursively convert dataclasses and lists into JSON-serializable primitives."""
    if isinstance(obj, list):
        return [to_jsonable(x) for x in obj]
    if hasattr(obj, "__dataclass_fields__"):
        return {k: to_jsonable(v) for k, v in asdict(obj).items()}
    return obj


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
        print(json.dumps(to_jsonable(result), indent=2))
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

    print(json.dumps(to_jsonable(result), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
