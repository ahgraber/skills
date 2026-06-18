#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "pytest>=8",
# ]
# ///
"""Tests for scripts/build-review-packet.py."""

import importlib.util
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "build-review-packet.py"


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


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    raise SystemExit(pytest.main([__file__, "-q", "--rootdir", here, "--confcutdir", here]))
