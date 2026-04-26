from __future__ import annotations

from pathlib import Path

from skills_mcp.dedup import dedup_skills
from skills_mcp.discovery import RootSpec


def test_dedup_no_collision(tmp_path: Path, make_skill):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    make_skill(root_a, "alpha")
    make_skill(root_b, "beta")
    report = dedup_skills([RootSpec("a", root_a), RootSpec("b", root_b)])
    names = sorted(s.display_name for s in report.resolved)
    assert names == ["alpha", "beta"]
    assert report.collapsed_symlinks == 0
    assert report.collapsed_hash == 0
    assert report.namespace_collisions == []


def test_dedup_collapses_symlinked_root(tmp_path: Path, make_skill):
    real = tmp_path / "real"
    make_skill(real, "shared")
    link = tmp_path / "link"
    link.symlink_to(real)
    report = dedup_skills([RootSpec("real", real), RootSpec("link", link)])
    assert len(report.resolved) == 1
    assert report.resolved[0].display_name == "shared"
    assert report.resolved[0].root_label == "real"
    assert report.collapsed_symlinks == 1
    assert report.collapsed_hash == 0


def test_dedup_collapses_byte_identical_distinct_paths(tmp_path: Path, make_skill):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    make_skill(root_a, "twin", body="Same body.\n")
    make_skill(root_b, "twin", body="Same body.\n")
    report = dedup_skills([RootSpec("a", root_a), RootSpec("b", root_b)])
    assert len(report.resolved) == 1
    assert report.resolved[0].root_label == "a"
    assert report.collapsed_hash == 1
    assert report.namespace_collisions == []


def test_dedup_namespaces_true_collisions(tmp_path: Path, make_skill):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    make_skill(root_a, "drift", body="Version one.\n")
    make_skill(root_b, "drift", body="Version two.\n")
    report = dedup_skills(
        [RootSpec("claude", root_a), RootSpec("agents", root_b)],
    )
    names = sorted(s.display_name for s in report.resolved)
    assert names == ["agents--drift", "drift"]

    bare = next(s for s in report.resolved if s.display_name == "drift")
    namespaced = next(s for s in report.resolved if s.display_name == "agents--drift")
    assert bare.root_label == "claude"
    assert bare.namespaced is False
    assert namespaced.root_label == "agents"
    assert namespaced.namespaced is True

    assert len(report.namespace_collisions) == 1
    name, labels = report.namespace_collisions[0]
    assert name == "drift"
    assert labels == ["claude", "agents"]


def test_dedup_three_way_collision(tmp_path: Path, make_skill):
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    make_skill(a, "x", body="one\n")
    make_skill(b, "x", body="two\n")
    make_skill(c, "x", body="three\n")
    report = dedup_skills(
        [RootSpec("claude", a), RootSpec("agents", b), RootSpec("cursor", c)],
    )
    names = sorted(s.display_name for s in report.resolved)
    assert names == ["agents--x", "cursor--x", "x"]
