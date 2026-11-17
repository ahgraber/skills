#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8.0.0",
# ]
# ///
"""Behavior tests for the jj skill's preflight script.

The jj binary is replaced by a fake runner that answers from a table, so the
tests assert the report and exit code for each repo state without a real repo.

Run: uv run tests/jj/test_jj_preflight.py
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "skills" / "jj" / "scripts" / "jj_preflight.py"
_spec = importlib.util.spec_from_file_location("jj_preflight", _MODULE_PATH)
assert _spec is not None
assert _spec.loader is not None
pf = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = pf
_spec.loader.exec_module(pf)


WC_DESCRIBED_FULL = "kxrpqwsv\t1a2b3c4d\tfalse\tfalse\tfeat(x): first"
WC_EMPTY_UNDESCRIBED = "kxrpqwsv\t1a2b3c4d\ttrue\tfalse\t"
WC_UNDESCRIBED_FULL = "kxrpqwsv\t1a2b3c4d\tfalse\tfalse\t"

FULL_CONFIG = {
    "user.name": "Human",
    "user.email": "h@x",
    'revset-aliases."immutable_heads()"': "builtin_immutable_heads() | remote_bookmarks()",
    "ui.conflict-marker-style": "git",
}


class FakeJJ:
    """Answer jj invocations from a table keyed by the first distinctive argument."""

    def __init__(
        self,
        root: Path,
        *,
        working_copy: str = WC_DESCRIBED_FULL,
        config: dict[str, str] | None = None,
        trunk: str = "main\n",
    ):
        self.root = root
        self.working_copy = working_copy
        self.config = config if config is not None else {"user.name": "Human", "user.email": "human@example.invalid"}
        self.trunk = trunk
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str], cwd: Path | None) -> tuple[int, str, str]:
        self.calls.append(args)
        if args == ["--version"]:
            return 0, "jj 0.41.0\n", ""
        if args == ["root"]:
            return 0, f"{self.root}\n", ""
        if args[:2] == ["config", "get"]:
            value = self.config.get(args[2])
            return (
                (0, f"{value}\n", "")
                if value is not None
                else (1, "", f"Config error: Value not found for {args[2]}\n")
            )
        if args[:3] == ["log", "-r", "@"]:
            return 0, self.working_copy + "\n", ""
        if args[:3] == ["log", "-r", "@-"]:
            return 0, "pzyxwvut\n", ""
        if args[:3] == ["diff", "-r", "@"]:
            return 0, "src/a.py\nsrc/b.py\n", ""
        if args[:2] == ["log", "-r"] and args[2].startswith("heads("):
            return 0, "feature\n", ""
        if args[:3] == ["log", "-r", "trunk()"]:
            return 0, self.trunk, ""
        if args[:2] == ["op", "log"]:
            return 0, "88ccc4bc882f\tdefault@\n", ""
        return 1, "", f"unexpected call {args}"


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    (tmp_path / ".jj").mkdir()
    (tmp_path / ".git").mkdir()
    return tmp_path


@pytest.fixture
def agent_key(tmp_path: Path) -> Path:
    key = tmp_path / "agent-key.pub"
    key.write_text("ssh-ed25519 AAAA test\n", encoding="utf-8")
    return key


@pytest.fixture
def agent_config(tmp_path: Path, agent_key: Path) -> Path:
    path = tmp_path / "agent.toml"
    path.write_text(f'[signing]\nbackend = "ssh"\nkey = "{agent_key}"\nbehavior = "own"\n', encoding="utf-8")
    return path


def test_parse_version_reads_triple():
    assert pf.parse_version("jj 0.41.0\n") == (0, 41, 0)
    assert pf.parse_version("garbage") is None


def test_teach_flag_detected_only_as_whole_line(repo: Path):
    assert pf.find_teach_flag(repo) is False
    (repo / "AGENTS.md").write_text("# Rules\n\njj: teach\n", encoding="utf-8")
    assert pf.find_teach_flag(repo) is True
    (repo / "AGENTS.md").write_text("mention of jj: teach mode in prose\n", encoding="utf-8")
    assert pf.find_teach_flag(repo) is False


def test_agent_config_is_optional_but_must_be_valid_when_present(tmp_path: Path, agent_config: Path, agent_key: Path):
    assert pf.check_agent_config(agent_config)[0] == "pass"
    assert pf.check_agent_config(tmp_path / "missing.toml")[0] == "warn"

    no_backend = tmp_path / "no-backend.toml"
    no_backend.write_text(f'[signing]\nkey = "{agent_key}"\n', encoding="utf-8")
    status, detail = pf.check_agent_config(no_backend)
    assert status == "fail"
    assert "ssh gpg gpgsm" in detail

    missing_key = tmp_path / "missing-key.toml"
    missing_key.write_text('[signing]\nbackend = "ssh"\nkey = "/nonexistent/agent-key"\n', encoding="utf-8")
    status, detail = pf.check_agent_config(missing_key)
    assert status == "fail"
    assert "does not exist" in detail

    key_id = tmp_path / "key-id.toml"
    key_id.write_text('[signing]\nbackend = "gpg"\nkey = "DEADBEEF"\n', encoding="utf-8")
    assert pf.check_agent_config(key_id)[0] == "pass"


def test_ok_report_carries_state(repo: Path, agent_config: Path):
    fake = FakeJJ(repo, config=FULL_CONFIG)
    report = pf.collect(fake, repo, agent_config)
    assert report.status == "ok"
    assert report.jj_version == "0.41.0"
    assert report.colocated is True
    assert report.op_id == "88ccc4bc882f"
    assert report.workspace == "default"
    assert report.bookmarks == ["feature"]
    assert report.trunk == ["main"]
    assert report.working_copy["description"] == "feat(x): first"
    assert all(c.status == "pass" for c in report.checks)


def test_base_is_at_when_agent_will_start_a_new_change(repo: Path, agent_config: Path):
    report = pf.collect(FakeJJ(repo, config=FULL_CONFIG), repo, agent_config)
    assert report.base == "kxrpqwsv"


def test_base_is_parent_when_at_is_empty_and_undescribed(repo: Path, agent_config: Path):
    report = pf.collect(FakeJJ(repo, config=FULL_CONFIG, working_copy=WC_EMPTY_UNDESCRIBED), repo, agent_config)
    assert report.status == "ok"
    assert report.base == "pzyxwvut"


def test_missing_identity_is_setup_required(repo: Path, agent_config: Path):
    fake = FakeJJ(repo, config={})
    report = pf.collect(fake, repo, agent_config)
    assert report.status == "setup-required"
    failed = {c.name for c in report.checks if c.status == "fail"}
    assert failed == {"user.name", "user.email"}


def test_undescribed_edits_need_a_decision(repo: Path, agent_config: Path):
    fake = FakeJJ(repo, working_copy=WC_UNDESCRIBED_FULL)
    report = pf.collect(fake, repo, agent_config)
    assert report.status == "decision-required"
    assert report.working_copy["files"] == ["src/a.py", "src/b.py"]


def test_setup_failure_outranks_decision(repo: Path, agent_config: Path):
    fake = FakeJJ(repo, working_copy=WC_UNDESCRIBED_FULL, config={})
    report = pf.collect(fake, repo, agent_config)
    assert report.status == "setup-required"


def test_missing_agent_config_only_warns(repo: Path, tmp_path: Path):
    report = pf.collect(FakeJJ(repo, config=FULL_CONFIG), repo, tmp_path / "missing.toml")
    assert report.status == "ok"
    assert {c.name for c in report.checks if c.status == "warn"} == {"agent-signing-config"}


def test_non_colocated_and_default_config_only_warn(repo: Path, agent_config: Path):
    (repo / ".git").rmdir()
    report = pf.collect(FakeJJ(repo), repo, agent_config)
    assert report.status == "ok"
    warned = {c.name for c in report.checks if c.status == "warn"}
    assert warned == {"colocated", "immutable-remote-bookmarks", "conflict-markers"}


def test_untracked_remote_bookmarks_alias_does_not_count(repo: Path, agent_config: Path):
    config = dict(FULL_CONFIG, **{'revset-aliases."immutable_heads()"': "trunk() | untracked_remote_bookmarks()"})
    report = pf.collect(FakeJJ(repo, config=config), repo, agent_config)
    assert {c.name for c in report.checks if c.status == "warn"} == {"immutable-remote-bookmarks"}


def test_missing_trunk_warns(repo: Path, agent_config: Path):
    report = pf.collect(FakeJJ(repo, config=FULL_CONFIG, trunk="\n"), repo, agent_config)
    assert report.trunk == []
    assert {c.name for c in report.checks if c.status == "warn"} == {"trunk"}


def test_unignored_worktrees_dir_warns(repo: Path, agent_config: Path, monkeypatch: pytest.MonkeyPatch):
    (repo / ".worktrees").mkdir()
    monkeypatch.setattr(pf, "git_ignores", lambda root, relative: False)
    report = pf.collect(FakeJJ(repo, config=FULL_CONFIG), repo, agent_config)
    assert {c.name for c in report.checks if c.status == "warn"} == {"worktrees-ignored"}
    monkeypatch.setattr(pf, "git_ignores", lambda root, relative: True)
    report = pf.collect(FakeJJ(repo, config=FULL_CONFIG), repo, agent_config)
    assert report.status == "ok"
    assert all(c.status == "pass" for c in report.checks)


def test_not_a_jj_repo(tmp_path: Path, agent_config: Path):
    def fake(args: list[str], cwd: Path | None) -> tuple[int, str, str]:
        if args == ["--version"]:
            return 0, "jj 0.41.0\n", ""
        return 1, "", 'Error: There is no jj repo in "."\n'

    report = pf.collect(fake, tmp_path, agent_config)
    assert report.status == "not-a-jj-repo"


def test_main_prints_json_and_maps_exit_codes(repo: Path, agent_config: Path, capsys: pytest.CaptureFixture[str]):
    fake = FakeJJ(repo, working_copy=WC_UNDESCRIBED_FULL)
    code = pf.main(["--repo", str(repo), "--agent-config", str(agent_config)], runner=fake, jj_found=True)
    out = capsys.readouterr().out
    assert code == pf.EXIT_DECISION
    payload = json.loads(out)
    assert payload["status"] == "decision-required"
    assert payload["base"] == "kxrpqwsv"

    code = pf.main(
        ["--repo", str(repo), "--agent-config", str(agent_config), "--format", "text"],
        runner=FakeJJ(repo, config=FULL_CONFIG),
        jj_found=True,
    )
    out = capsys.readouterr().out
    assert code == pf.EXIT_OK
    assert out.startswith("status: ok")
    assert "base: kxrpqwsv" in out


def test_main_without_jj_binary(tmp_path: Path, agent_config: Path):
    code = pf.main(
        ["--repo", str(tmp_path), "--agent-config", str(agent_config)], runner=FakeJJ(tmp_path), jj_found=False
    )
    assert code == pf.EXIT_NOT_JJ


if __name__ == "__main__":
    here = Path(__file__).resolve().parent
    sys.exit(pytest.main([str(Path(__file__)), "--rootdir", str(here), "--confcutdir", str(here), "-q"]))
