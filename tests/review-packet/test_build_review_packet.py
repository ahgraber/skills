#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8",
# ]
# ///
"""Tests for scripts/build_review_packet.py."""

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "build_review_packet.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("build_review_packet", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


brp = _load_module()


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)  # noqa: S603


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    # Isolate from the developer's global config (commit signing would fail here).
    _git(repo, "config", "commit.gpgsign", "false")
    _git(repo, "config", "tag.gpgsign", "false")
    (repo / "a.txt").write_text("one\n")
    _git(repo, "add", "a.txt")
    _git(repo, "commit", "-qm", "init")
    return repo


def _run(repo: Path, *cli: str, out: Path) -> dict:
    args = brp.parse_args([*cli, "--repo", str(repo), "--out", str(out)])
    return brp.build_packet(args)


def test_staged_diff_without_source_of_truth(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("one\ntwo\n")
    _git(repo, "add", "a.txt")
    out = tmp_path / "packet.md"
    result = _run(repo, "--staged", out=out)
    assert result["changed_files"] == 1
    assert result["has_source_of_truth"] is False
    text = out.read_text()
    assert "NO SOURCE OF TRUTH" in text
    assert "two" in text  # the added line is present in the diff


def test_intent_sets_source_of_truth(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("one\ntwo\n")
    _git(repo, "add", "a.txt")
    out = tmp_path / "packet.md"
    result = _run(repo, "--staged", "--intent", "add a second line", out=out)
    assert result["has_source_of_truth"] is True
    assert "add a second line" in out.read_text()


def test_missing_include_only_is_not_source_of_truth(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    _git(repo, "add", "a.txt")
    out = tmp_path / "packet.md"
    result = _run(repo, "--staged", "--include", str(tmp_path / "absent.md"), out=out)
    assert result["has_source_of_truth"] is False
    assert "Missing include" in out.read_text()


def test_readable_include_is_source_of_truth(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    _git(repo, "add", "a.txt")
    spec = tmp_path / "spec.md"
    spec.write_text("THE CONTRACT")
    out = tmp_path / "packet.md"
    result = _run(repo, "--staged", "--include", str(spec), out=out)
    assert result["has_source_of_truth"] is True
    assert "THE CONTRACT" in out.read_text()


def test_diff_truncation_is_announced(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "big.txt").write_text("\n".join(str(i) for i in range(5000)) + "\n")
    _git(repo, "add", "big.txt")
    out = tmp_path / "packet.md"
    args = brp.parse_args(["--staged", "--repo", str(repo), "--out", str(out), "--max-diff-bytes", "500"])
    result = brp.build_packet(args)
    assert result["diff_truncated"] is True
    assert "diff truncated" in out.read_text()


def test_non_git_repo_errors(tmp_path):
    with pytest.raises(SystemExit):
        _run(tmp_path, "--staged", out=tmp_path / "packet.md")


def _run_default_out(repo: Path) -> Path:
    args = brp.parse_args(["--staged", "--repo", str(repo)])
    return Path(brp.build_packet(args)["packet_path"])


@pytest.mark.parametrize(
    ("present", "expected"),
    [
        ([".review", "._scratch", ".scratch"], ".review"),
        (["._scratch", ".scratch"], "._scratch"),
        ([".scratch"], ".scratch"),
    ],
)
def test_default_out_uses_first_existing_repo_dir(tmp_path, present, expected):
    repo = _init_repo(tmp_path)
    for name in present:
        (repo / name).mkdir()
    assert _run_default_out(repo).parent == repo / expected


def test_default_out_resolves_repo_root_from_subdir(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / ".review").mkdir()
    (repo / "sub").mkdir()
    assert _run_default_out(repo / "sub").parent == repo / ".review"


def test_default_out_falls_back_to_tmpdir(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    tmp = tmp_path / "tmp"
    tmp.mkdir()
    monkeypatch.setattr(brp.tempfile, "tempdir", str(tmp))
    out = _run_default_out(repo)
    assert out.parent == tmp
    assert not (repo / ".review").exists()


def test_branch_is_reported_in_json_and_packet(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-qb", "feature/x")
    (repo / "a.txt").write_text("changed\n")
    _git(repo, "add", "a.txt")
    out = tmp_path / "packet.md"
    result = _run(repo, "--staged", out=out)
    assert result["branch"] == "feature/x"
    assert "- branch: feature/x" in out.read_text()


def test_state_path_sits_beside_packet_and_is_keyed_by_repo_and_branch(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-qb", "feature/x")
    (repo / "a.txt").write_text("changed\n")
    _git(repo, "add", "a.txt")
    out = tmp_path / "out" / "packet.md"
    result = _run(repo, "--staged", out=out)
    state = Path(result["state_path"])
    assert state.parent == out.parent
    assert "repo" in state.name
    assert "feature-x" in state.name
    assert result["state_exists"] is False
    assert result["stale_closed_partitions"] == []


def _write_state(path: Path, partitions: list[dict]) -> None:
    path.write_text(json.dumps({"version": 1, "partitions": partitions}))


def _head(repo: Path) -> str:
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), "rev-parse", "HEAD"], check=True, capture_output=True, text=True
    ).stdout.strip()


def _state_run(repo: Path, tmp_path: Path, partitions_for_head) -> dict:
    out = tmp_path / "out" / "packet.md"
    out.parent.mkdir(exist_ok=True)
    first = _run(repo, "--worktree", out=out)
    _write_state(Path(first["state_path"]), partitions_for_head(_head(repo)))
    return first


def test_closed_partition_with_unchanged_paths_is_not_stale(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "b.txt").write_text("other\n")
    _state_run(
        repo,
        tmp_path,
        lambda head: [{"id": "P1", "status": "closed", "paths": ["a.txt"], "explored": [{"head": head}]}],
    )
    result = _run(repo, "--worktree", out=tmp_path / "out" / "packet.md")
    assert result["state_exists"] is True
    assert result["stale_closed_partitions"] == []


def test_closed_partition_whose_path_changed_is_stale(tmp_path):
    repo = _init_repo(tmp_path)
    _state_run(
        repo,
        tmp_path,
        lambda head: [
            {"id": "P1", "status": "closed", "paths": ["a.txt"], "explored": [{"head": head}]},
            {"id": "P2", "status": "open", "paths": ["a.txt"], "explored": [{"head": head}]},
        ],
    )
    (repo / "a.txt").write_text("edited after the partition closed\n")
    result = _run(repo, "--worktree", out=tmp_path / "out" / "packet.md")
    assert result["stale_closed_partitions"] == ["P1"]


@pytest.mark.parametrize(
    "partition",
    [
        {"id": "P1", "status": "closed", "paths": [], "explored": [{"head": "HEAD"}]},
        {"id": "P1", "status": "closed", "paths": ["a.txt"], "explored": []},
        {"id": "P1", "status": "closed", "paths": ["a.txt"], "explored": [{"head": "0" * 40}]},
    ],
    ids=["no-paths", "never-explored", "head-missing"],
)
def test_closed_partition_without_usable_history_is_stale(tmp_path, partition):
    repo = _init_repo(tmp_path)
    (repo / "b.txt").write_text("other\n")
    _state_run(repo, tmp_path, lambda _head: [partition])
    result = _run(repo, "--worktree", out=tmp_path / "out" / "packet.md")
    assert result["stale_closed_partitions"] == ["P1"]


def test_malformed_state_is_reported_not_raised(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    out = tmp_path / "out" / "packet.md"
    out.parent.mkdir()
    first = _run(repo, "--worktree", out=out)
    Path(first["state_path"]).write_text("{not json")
    result = _run(repo, "--worktree", out=out)
    assert result["state_exists"] is True
    assert "state_error" in result


def test_output_dir_is_tmp_flags_the_fallback(tmp_path, monkeypatch):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    _git(repo, "add", "a.txt")
    tmp = tmp_path / "tmp"
    tmp.mkdir()
    monkeypatch.setattr(brp.tempfile, "tempdir", str(tmp))
    args = brp.parse_args(["--staged", "--repo", str(repo)])
    assert brp.build_packet(args)["output_dir_is_tmp"] is True
    (repo / ".review").mkdir()
    assert brp.build_packet(args)["output_dir_is_tmp"] is False


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    raise SystemExit(pytest.main([__file__, "-q", "--rootdir", here, "--confcutdir", here]))
