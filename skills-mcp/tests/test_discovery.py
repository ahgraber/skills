from __future__ import annotations

from pathlib import Path

from skills_mcp.discovery import (
    RootSpec,
    discover_roots,
    parse_env_roots,
    parse_root_arg,
)


def test_parse_root_arg_path_only(tmp_path: Path):
    spec = parse_root_arg(str(tmp_path / "myrepo" / "skills"))
    assert spec.label == "myrepo"
    assert spec.path == tmp_path / "myrepo" / "skills"


def test_parse_root_arg_label_path(tmp_path: Path):
    spec = parse_root_arg(f"team={tmp_path}/x")
    assert spec.label == "team"
    assert spec.path == tmp_path / "x"


def test_parse_root_arg_label_safe():
    spec = parse_root_arg("weird/label=/tmp/x")
    assert "/" not in spec.label
    assert spec.label.isascii()


def test_parse_env_roots_colon_separated(tmp_path: Path):
    a = tmp_path / "a" / "skills"
    b = tmp_path / "b" / "skills"
    raw = f"{a}:lab={b}"
    specs = parse_env_roots(raw)
    assert [s.label for s in specs] == ["a", "lab"]
    assert [s.path for s in specs] == [a, b]


def test_parse_env_roots_empty(monkeypatch):
    monkeypatch.delenv("SKILLS_MCP_ROOTS", raising=False)
    assert parse_env_roots("") == []
    assert parse_env_roots(None) == []


def test_discover_roots_filters_nonexistent(tmp_path: Path):
    real = tmp_path / "real"
    real.mkdir()
    fake = tmp_path / "missing"
    extras = [RootSpec("real", real), RootSpec("fake", fake)]
    out = discover_roots(extra=extras, include_known=False, include_env=False)
    assert [s.label for s in out] == ["real"]


def test_discover_roots_dedups_by_realpath(tmp_path: Path):
    real = tmp_path / "skills"
    real.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(real)
    extras = [RootSpec("a", real), RootSpec("b", link)]
    out = discover_roots(extra=extras, include_known=False, include_env=False)
    assert len(out) == 1
    assert out[0].label == "a"  # First wins.


def test_discover_roots_extra_precedes_known(tmp_path: Path):
    extra = tmp_path / "extra"
    extra.mkdir()
    out = discover_roots(
        extra=[RootSpec("extra", extra)],
        include_known=True,
        include_env=False,
    )
    assert out[0].label == "extra"
