#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "pytest>=8.0.0",
# ]
# ///
"""Regression tests for spec-kit's common.sh.

common.sh is pure function definitions, so each test sources it in a bash
subprocess and exercises one function — keeping the repo's single (pytest)
test convention rather than introducing a shell-test harness. common.sh is
symlinked into ~10 spec-kit-* sibling skills, so this is shared infrastructure.

Run: uv run tests/spec-kit/test_common.py
"""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest

COMMON_SH = Path(__file__).resolve().parents[2] / "skills" / "spec-kit" / "scripts" / "common.sh"
_GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": "/dev/null", "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_TERMINAL_PROMPT": "0"}


def _bash(snippet: str, *, cwd: Path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "SPECIFY_FEATURE"}
    if extra_env:
        env.update(extra_env)
    script = f'source "{COMMON_SH}"\n{snippet}'
    return subprocess.run(["bash", "-c", script], cwd=str(cwd), env=env, capture_output=True, text=True)  # noqa: S603, S607


def _mkspecs(root: Path, *names: str) -> None:
    for name in names:
        (root / "specs" / name).mkdir(parents=True, exist_ok=True)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=str(cwd), env=_GIT_ENV, check=True, capture_output=True, text=True)  # noqa: S603, S607


def _git_repo(root: Path, branch: str) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    _git(root, "init", "-q")
    _git(root, "-c", "user.email=t@e", "-c", "user.name=t", "commit", "--allow-empty", "-q", "-m", "init")
    _git(root, "switch", "-q", "-c", branch)
    return root


# --- get_current_branch ------------------------------------------------------


def test_specify_feature_env_takes_precedence(tmp_path):
    result = _bash("get_current_branch", cwd=tmp_path, extra_env={"SPECIFY_FEATURE": "003-from-env"})

    assert result.stdout.strip() == "003-from-env"


def test_get_current_branch_uses_git_branch(tmp_path):
    repo = _git_repo(tmp_path / "repo", "007-feature")

    result = _bash("get_current_branch", cwd=repo)

    assert result.stdout.strip() == "007-feature"


def test_get_current_branch_non_git_picks_highest_numbered_spec(tmp_path):
    # 008/012 also exercise base-10 normalization (`10#`), which guards against
    # 0-prefixed numbers being parsed as invalid octal.
    _mkspecs(tmp_path, "008-alpha", "012-beta")

    result = _bash(
        'get_repo_root() { echo "$FAKE_ROOT"; }\nget_current_branch',
        cwd=tmp_path,
        extra_env={"FAKE_ROOT": str(tmp_path)},
    )

    assert result.stdout.strip() == "012-beta"


def test_get_current_branch_non_git_no_specs_returns_main(tmp_path):
    result = _bash(
        'get_repo_root() { echo "$FAKE_ROOT"; }\nget_current_branch',
        cwd=tmp_path,
        extra_env={"FAKE_ROOT": str(tmp_path)},
    )

    assert result.stdout.strip() == "main"


# --- get_repo_root -----------------------------------------------------------


def test_get_repo_root_in_git_repo_returns_toplevel(tmp_path):
    repo = _git_repo(tmp_path / "repo", "001-x")

    result = _bash("get_repo_root", cwd=repo)

    assert os.path.samefile(result.stdout.strip(), repo)


# --- find_feature_dir_by_prefix ----------------------------------------------


def test_find_feature_dir_no_numeric_prefix_falls_back_to_exact(tmp_path):
    result = _bash(f'find_feature_dir_by_prefix "{tmp_path}" "myfeature"', cwd=tmp_path)

    assert result.stdout.strip() == f"{tmp_path}/specs/myfeature"


def test_find_feature_dir_single_match(tmp_path):
    _mkspecs(tmp_path, "004-the-feature")

    result = _bash(f'find_feature_dir_by_prefix "{tmp_path}" "004-anything"', cwd=tmp_path)

    assert result.stdout.strip() == f"{tmp_path}/specs/004-the-feature"


def test_find_feature_dir_no_match_returns_branch_path(tmp_path):
    _mkspecs(tmp_path, "005-other")

    result = _bash(f'find_feature_dir_by_prefix "{tmp_path}" "004-missing"', cwd=tmp_path)

    assert result.stdout.strip() == f"{tmp_path}/specs/004-missing"


def test_find_feature_dir_multiple_matches_errors(tmp_path):
    _mkspecs(tmp_path, "004-alpha", "004-beta")

    result = _bash(f'find_feature_dir_by_prefix "{tmp_path}" "004-x"', cwd=tmp_path)

    assert "Multiple spec directories" in result.stderr
    assert result.stdout.strip() == f"{tmp_path}/specs/004-x"


# --- check_feature_branch ----------------------------------------------------


def test_check_feature_branch_non_git_warns_and_passes(tmp_path):
    result = _bash('check_feature_branch "main" "false"', cwd=tmp_path)

    assert result.returncode == 0
    assert "skipped branch validation" in result.stderr


def test_check_feature_branch_rejects_non_feature_branch(tmp_path):
    result = _bash('check_feature_branch "main" "true"', cwd=tmp_path)

    assert result.returncode == 1
    assert "Not on a feature branch" in result.stderr


def test_check_feature_branch_accepts_feature_branch(tmp_path):
    result = _bash('check_feature_branch "001-feature" "true"', cwd=tmp_path)

    assert result.returncode == 0


# --- get_feature_dir ---------------------------------------------------------


def test_get_feature_dir_composes_path(tmp_path):
    result = _bash('get_feature_dir "/root" "001-x"', cwd=tmp_path)

    assert result.stdout.strip() == "/root/specs/001-x"


if __name__ == "__main__":
    _here = str(Path(__file__).resolve().parent)
    raise SystemExit(
        pytest.main([str(Path(__file__).resolve()), "-v", "-p", "no:cacheprovider", "--rootdir", _here, "--confcutdir", _here])
    )
