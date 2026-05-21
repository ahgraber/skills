#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "pytest>=8.0.0",
# ]
# ///
"""Regression tests for sdd's find-specs-roots.py.

Behavior-level: exercise the discovery/parse functions against a tmp tree, and
drive main() via --workspace (which overrides the git/cwd anchor) so the JSON
output is deterministic. find-specs-roots.py is stdlib-only.

Run: uv run tests/sdd/test_find_specs_roots.py
"""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "skills" / "sdd" / "scripts" / "find-specs-roots.py"
_spec = importlib.util.spec_from_file_location("find_specs_roots", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None
fsr = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = fsr
_spec.loader.exec_module(fsr)


def _git_init(repo: Path) -> None:
    repo.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=str(repo), check=True, capture_output=True, text=True)  # noqa: S603, S607


# --- is_inside ---------------------------------------------------------------


def test_is_inside_descendant(tmp_path):
    assert fsr.is_inside(tmp_path / "a" / "b", tmp_path) is True


def test_is_inside_self(tmp_path):
    assert fsr.is_inside(tmp_path, tmp_path) is True


def test_is_inside_outside(tmp_path):
    assert fsr.is_inside(tmp_path.parent / "sibling-xyz", tmp_path) is False


# --- walk_for_dirs -----------------------------------------------------------


def test_walk_finds_named_dir(tmp_path):
    (tmp_path / "x" / ".specs").mkdir(parents=True)

    found = fsr.walk_for_dirs(tmp_path, ".specs", max_depth=None)

    assert [str(p) for p in found] == [str((tmp_path / "x" / ".specs").resolve())]


def test_walk_skips_excluded_dirs(tmp_path):
    (tmp_path / "pkg" / ".specs").mkdir(parents=True)
    (tmp_path / "node_modules" / ".specs").mkdir(parents=True)

    found = {str(p) for p in fsr.walk_for_dirs(tmp_path, ".specs", max_depth=None)}

    assert str((tmp_path / "pkg" / ".specs").resolve()) in found
    assert all("node_modules" not in p for p in found)


def test_walk_respects_max_depth(tmp_path):
    (tmp_path / "specs").mkdir()  # depth 1
    (tmp_path / "a" / "specs").mkdir(parents=True)  # depth 2
    (tmp_path / "a" / "b" / "specs").mkdir(parents=True)  # depth 3

    found = {str(p) for p in fsr.walk_for_dirs(tmp_path, "specs", max_depth=2)}

    assert str((tmp_path / "specs").resolve()) in found
    assert str((tmp_path / "a" / "specs").resolve()) in found
    assert str((tmp_path / "a" / "b" / "specs").resolve()) not in found


# --- parse_pointer_file ------------------------------------------------------


def test_parse_entries_and_comments(tmp_path):
    pointer = tmp_path / "SPECS_ROOT"
    pointer.write_text("# header\n\nspecs/here  # primary\n../other   // secondary\n", encoding="utf-8")

    entries, reason, _ = fsr.parse_pointer_file(pointer)

    assert reason is None
    assert entries == [("specs/here", "primary"), ("../other", "secondary")]


def test_parse_comment_earliest_marker_wins(tmp_path):
    pointer = tmp_path / "SPECS_ROOT"
    pointer.write_text("path // slash # hash\n", encoding="utf-8")

    entries, _, _ = fsr.parse_pointer_file(pointer)

    assert entries == [("path", "slash # hash")]


def test_parse_empty_is_malformed_empty(tmp_path):
    pointer = tmp_path / "SPECS_ROOT"
    pointer.write_text("# only a comment\n\n", encoding="utf-8")

    entries, reason, _ = fsr.parse_pointer_file(pointer)

    assert entries == []
    assert reason == "empty"


def test_parse_unreadable_file(tmp_path):
    entries, reason, detail = fsr.parse_pointer_file(tmp_path / "does-not-exist")

    assert entries == []
    assert reason == "unreadable"
    assert detail


# --- resolve_pointer_target --------------------------------------------------


def test_resolve_relative_to_marker_dir(tmp_path):
    assert fsr.resolve_pointer_target("sub/dir", tmp_path) == (tmp_path / "sub" / "dir").resolve()


def test_resolve_absolute_path(tmp_path):
    abs_target = tmp_path / "abs"

    assert fsr.resolve_pointer_target(str(abs_target), tmp_path / "marker") == abs_target.resolve()


# --- analyze_pointer ---------------------------------------------------------


def test_analyze_pointer_absent_returns_none(tmp_path):
    assert fsr.analyze_pointer(tmp_path, tmp_path) is None


def test_analyze_pointer_empty_is_malformed(tmp_path):
    (tmp_path / "SPECS_ROOT").write_text("# nothing here\n", encoding="utf-8")

    info = fsr.analyze_pointer(tmp_path, tmp_path)

    assert info.malformed is True
    assert info.malformed_reason == "empty"


def test_analyze_pointer_targets_inside_and_outside(tmp_path):
    anchor = tmp_path / "ws"
    marker = anchor / ".specs"
    marker.mkdir(parents=True)
    (marker / "inside").mkdir()
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (marker / "SPECS_ROOT").write_text(f"inside\n{outside}\n", encoding="utf-8")

    info = fsr.analyze_pointer(marker, anchor)

    by_raw = {t.raw: t for t in info.targets}
    assert by_raw["inside"].exists and by_raw["inside"].is_dir
    assert by_raw["inside"].outside_workspace is False
    assert by_raw[str(outside)].outside_workspace is True


# --- analyze_explicit --------------------------------------------------------


def test_analyze_explicit_existing_inside(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()

    info = fsr.analyze_explicit(str(sub), tmp_path)

    assert info.exists is True
    assert info.outside_workspace is False


def test_analyze_explicit_nonexistent(tmp_path):
    info = fsr.analyze_explicit(str(tmp_path / "nope"), tmp_path)

    assert info.exists is False


def test_analyze_explicit_outside_workspace(tmp_path):
    anchor = tmp_path / "ws"
    anchor.mkdir()
    other = tmp_path / "outside"
    other.mkdir()

    info = fsr.analyze_explicit(str(other), anchor)

    assert info.outside_workspace is True


# --- find_anchor -------------------------------------------------------------


def test_find_anchor_override(tmp_path):
    anchor, source = fsr.find_anchor(tmp_path)

    assert source == "override"
    assert anchor == tmp_path.resolve()


def test_find_anchor_git_toplevel(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
    _git_init(repo)
    monkeypatch.chdir(repo)

    anchor, source = fsr.find_anchor(None)

    assert source == "git"
    assert os.path.samefile(anchor, repo)


def test_find_anchor_cwd_when_not_git(tmp_path, monkeypatch):
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.setenv("GIT_CONFIG_SYSTEM", "/dev/null")
    monkeypatch.chdir(tmp_path)

    anchor, source = fsr.find_anchor(None)

    assert source == "cwd"
    assert os.path.samefile(anchor, tmp_path)


# --- main (integration) ------------------------------------------------------


def test_main_discovers_dot_specs(tmp_path, monkeypatch, capsys):
    (tmp_path / ".specs").mkdir()
    monkeypatch.setattr(sys, "argv", ["find-specs-roots.py", "--workspace", str(tmp_path)])

    rc = fsr.main()

    out = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert any(c["path"].endswith("/.specs") for c in out["dot_specs_candidates"])
    assert out["fallback_used"] is False


def test_main_falls_back_to_specs(tmp_path, monkeypatch, capsys):
    (tmp_path / "pkg" / "specs").mkdir(parents=True)
    monkeypatch.setattr(sys, "argv", ["find-specs-roots.py", "--workspace", str(tmp_path)])

    fsr.main()

    out = json.loads(capsys.readouterr().out)
    assert out["fallback_used"] is True
    assert any(c["path"].endswith("/specs") for c in out["specs_fallback_candidates"])


def test_main_explicit_skips_discovery(tmp_path, monkeypatch, capsys):
    (tmp_path / ".specs").mkdir()  # present, but must be ignored when --explicit is given
    target = tmp_path / "chosen"
    target.mkdir()
    monkeypatch.setattr(sys, "argv", ["find-specs-roots.py", "--workspace", str(tmp_path), "--explicit", str(target)])

    fsr.main()

    out = json.loads(capsys.readouterr().out)
    assert out["explicit"]["raw"] == str(target)
    assert out["dot_specs_candidates"] == []


if __name__ == "__main__":
    _here = str(Path(__file__).resolve().parent)
    raise SystemExit(
        pytest.main([str(Path(__file__).resolve()), "-v", "-p", "no:cacheprovider", "--rootdir", _here, "--confcutdir", _here])
    )
