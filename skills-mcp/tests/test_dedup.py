from __future__ import annotations

from pathlib import Path

from skills_mcp.dedup import dedup_skills
from skills_mcp.discovery import RootSpec


def test_dedup_no_collision(tmp_path: Path, make_skill):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    make_skill(root_a, "alpha")
    make_skill(root_b, "beta")
    skills = dedup_skills([RootSpec("a", root_a), RootSpec("b", root_b)])
    assert sorted(s.display_name for s in skills) == ["alpha", "beta"]


def test_dedup_collapses_symlinked_root(tmp_path: Path, make_skill):
    real = tmp_path / "real"
    make_skill(real, "shared")
    link = tmp_path / "link"
    link.symlink_to(real)
    skills = dedup_skills([RootSpec("real", real), RootSpec("link", link)])
    assert len(skills) == 1
    assert skills[0].display_name == "shared"
    assert skills[0].root_label == "real"


def test_dedup_collapses_byte_identical_distinct_paths(tmp_path: Path, make_skill):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    make_skill(root_a, "twin", body="Same body.\n")
    make_skill(root_b, "twin", body="Same body.\n")
    skills = dedup_skills([RootSpec("a", root_a), RootSpec("b", root_b)])
    assert len(skills) == 1
    assert skills[0].root_label == "a"


def test_dedup_namespaces_true_collisions(tmp_path: Path, make_skill):
    root_a = tmp_path / "a"
    root_b = tmp_path / "b"
    make_skill(root_a, "drift", body="Version one.\n")
    make_skill(root_b, "drift", body="Version two.\n")
    skills = dedup_skills([RootSpec("claude", root_a), RootSpec("agents", root_b)])
    assert sorted(s.display_name for s in skills) == ["agents--drift", "drift"]

    bare = next(s for s in skills if s.display_name == "drift")
    namespaced = next(s for s in skills if s.display_name == "agents--drift")
    assert bare.root_label == "claude"
    assert namespaced.root_label == "agents"


def test_dedup_three_way_collision(tmp_path: Path, make_skill):
    a, b, c = tmp_path / "a", tmp_path / "b", tmp_path / "c"
    make_skill(a, "x", body="one\n")
    make_skill(b, "x", body="two\n")
    make_skill(c, "x", body="three\n")
    skills = dedup_skills(
        [RootSpec("claude", a), RootSpec("agents", b), RootSpec("cursor", c)],
    )
    assert sorted(s.display_name for s in skills) == ["agents--x", "cursor--x", "x"]
