#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8",
# ]
# ///
"""Tests for skills/sdd/scripts/check_verify_ignored.py."""

import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "sdd" / "scripts" / "check_verify_ignored.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_verify_ignored", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cvi = _load_module()


def _specs(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "-C", str(repo), "init", "-q"], check=True)  # noqa: S603
    specs = repo / ".specs"
    (specs / "changes" / "add-thing").mkdir(parents=True)
    return specs


def _run(specs: Path, *flags: str, capsys) -> dict:
    assert cvi.main([str(specs), *flags]) == 0
    return json.loads(capsys.readouterr().out)


def test_first_run_when_nothing_ignores_and_no_runs_exist(tmp_path, capsys):
    result = _run(_specs(tmp_path), capsys=capsys)
    assert result == {"ignored": False, "rule": None, "verify_dirs": [], "first_run": True}


def test_add_writes_one_rule_to_the_specs_root_gitignore(tmp_path, capsys):
    specs = _specs(tmp_path)
    result = _run(specs, "--add", capsys=capsys)
    assert result["ignored"] is True
    assert result["first_run"] is False
    assert (specs / ".gitignore").read_text() == ".verify/\n"
    _run(specs, "--add", capsys=capsys)
    assert (specs / ".gitignore").read_text() == ".verify/\n"


def test_add_appends_after_existing_rules_without_a_trailing_newline(tmp_path, capsys):
    specs = _specs(tmp_path)
    (specs / ".gitignore").write_text("*.tmp")
    _run(specs, "--add", capsys=capsys)
    assert (specs / ".gitignore").read_text() == "*.tmp\n.verify/\n"


def test_a_rule_at_the_repo_root_counts(tmp_path, capsys):
    specs = _specs(tmp_path)
    (specs.parent / ".gitignore").write_text("**/.verify/\n")
    result = _run(specs, capsys=capsys)
    assert result["ignored"] is True
    assert ".gitignore" in result["rule"]


def test_an_existing_run_directory_means_the_user_already_chose(tmp_path, capsys):
    specs = _specs(tmp_path)
    (specs / "changes" / "add-thing" / ".verify").mkdir()
    result = _run(specs, capsys=capsys)
    assert result["ignored"] is False
    assert result["first_run"] is False
    assert len(result["verify_dirs"]) == 1


def test_outside_a_git_work_tree_is_an_error(tmp_path, capsys):
    plain = tmp_path / "plain" / ".specs"
    plain.mkdir(parents=True)
    assert cvi.main([str(plain)]) == 2
    assert "error" in json.loads(capsys.readouterr().out)


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    raise SystemExit(pytest.main([__file__, "-q", "--rootdir", here, "--confcutdir", here]))
