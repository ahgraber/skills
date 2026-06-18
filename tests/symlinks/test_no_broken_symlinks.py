#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "pytest>=8",
# ]
# ///
"""Guard: every symlink under skills/ must resolve to an existing in-repo path.

`npx skills` (vercel-labs/skills) installs a skill by shallow-cloning the whole
repo and copying the skill dir with `cp(..., {dereference: true})`. A symlink
whose target is missing in the clone is skipped with a warning, silently
dropping the file from the installed skill. A symlink whose target escapes the
repo is never in the clone at all. Either way the installed skill breaks at
runtime. This test fails fast on both, so shared-script symlinks (e.g. the
sdd/spec-kit families and build-review-packet) stay installable.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"


def _symlinks() -> list[Path]:
    return sorted(p for p in SKILLS.rglob("*") if p.is_symlink())


def test_no_broken_symlinks() -> None:
    broken = []
    for link in _symlinks():
        target = (link.parent / link.readlink()).resolve()
        if not target.exists():
            broken.append(f"{link.relative_to(REPO)} -> {link.readlink()}")
    assert not broken, "broken symlinks (will be dropped on install):\n" + "\n".join(broken)


def test_symlink_targets_stay_in_repo() -> None:
    escapes = []
    for link in _symlinks():
        target = (link.parent / link.readlink()).resolve()
        if not target.is_relative_to(REPO):
            escapes.append(f"{link.relative_to(REPO)} -> {target}")
    assert not escapes, "symlink targets escape the repo (absent from the clone):\n" + "\n".join(escapes)


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    raise SystemExit(pytest.main([__file__, "-q", "--rootdir", here, "--confcutdir", here]))
