#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8",
# ]
# ///
"""Tests for scripts/build_review_packet.py."""

import importlib.util
import itertools
import json
from pathlib import Path
import subprocess
import sys

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
    _git(repo, "init", "-q", "-b", "main")
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


def test_state_fields_are_not_in_the_packet_json(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    result = _run(repo, "--worktree", out=tmp_path / "packet.md")
    for key in ("state_path", "state_exists", "needs_exploring", "output_dir_is_tmp"):
        assert key not in result


def test_index_gives_line_ranges_for_sections_and_files(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("one\ntwo\n")
    (repo / "b.txt").write_text("bee\n")
    _git(repo, "add", "a.txt", "b.txt")
    out = tmp_path / "packet.md"
    result = _run(repo, "--staged", "--intent", "the intent", out=out)
    lines = out.read_text().split("\n")
    sections = result["index"]["sections"]
    assert list(sections) == ["Metadata", "Changed files (name-status)", "Diff", "Source of truth"]
    for name, (first, last) in sections.items():
        assert lines[first - 1] == f"## {name}"
        assert first <= last <= len(lines)
    files = result["index"]["files"]
    assert set(files) == {"a.txt", "b.txt"}
    for path, (first, last) in files.items():
        assert lines[first - 1] == f"diff --git a/{path} b/{path}"
        assert sections["Diff"][0] < first <= last <= sections["Diff"][1]
    assert files["a.txt"][1] < files["b.txt"][0]


def test_headings_inside_an_included_spec_are_not_packet_sections(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    spec = tmp_path / "spec.md"
    spec.write_text("# Spec\n\n## Requirements\n\nThe system SHALL work.\n\n## Diff\n\nnot the packet's diff\n")
    out = tmp_path / "packet.md"
    result = _run(repo, "--worktree", "--include", str(spec), out=out)
    lines = out.read_text().split("\n")
    sections = result["index"]["sections"]
    assert list(sections) == ["Metadata", "Changed files (name-status)", "Diff", "Source of truth"]
    first, last = sections["Source of truth"]
    assert "The system SHALL work." in "\n".join(lines[first - 1 : last])
    assert "a.txt" in result["index"]["files"]


def test_index_decodes_quoted_paths_and_keeps_ranges_apart(tmp_path):
    repo = _init_repo(tmp_path)
    names = ["café.txt", "tab\tname.txt", 'quote"name.txt', "line\nname.txt", "with space.txt", "z.txt"]
    for name in names:
        (repo / name).write_text(f"content of {name!r}\n")
    _git(repo, "add", "--", *names)
    out = tmp_path / "packet.md"
    result = _run(repo, "--staged", out=out)
    lines = out.read_text().split("\n")
    files = result["index"]["files"]
    assert set(files) == set(names)
    spans = sorted(files.values())
    for (_, last), (next_first, _) in itertools.pairwise(spans):
        assert last < next_first
    for name, (first, last) in files.items():
        assert lines[first - 1].startswith("diff --git ")
        assert any(repr(name) in line for line in lines[first - 1 : last])


def test_index_keys_a_renamed_file_by_its_new_path(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "mv", "a.txt", "renamed a.txt")
    result = _run(repo, "--staged", out=tmp_path / "packet.md")
    assert list(result["index"]["files"]) == ["renamed a.txt"]


def test_packet_tokens_estimates_the_packet_size(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    out = tmp_path / "packet.md"
    result = _run(repo, "--worktree", out=out)
    assert result["packet_tokens"] == len(out.read_bytes()) // 4


def test_diff_comes_before_the_source_of_truth(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    _git(repo, "add", "a.txt")
    out = tmp_path / "packet.md"
    _run(repo, "--staged", "--intent", "the intent", out=out)
    text = out.read_text()
    assert text.index("## Diff") < text.index("## Source of truth")


def test_a_missing_include_is_reported_even_with_an_intent(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    _git(repo, "add", "a.txt")
    missing = tmp_path / "absent.md"
    result = _run(repo, "--staged", "--intent", "the intent", "--include", str(missing), out=tmp_path / "packet.md")
    assert result["has_source_of_truth"] is True
    assert result["missing_includes"] == [str(missing)]


def test_an_unknown_base_ref_is_an_error_that_names_it(tmp_path, capsys):
    repo = _init_repo(tmp_path)
    code = brp.main(["--base", "no-such-ref", "--repo", str(repo), "--out", str(tmp_path / "packet.md")])
    assert code == 1
    err = json.loads(capsys.readouterr().err)["error"]
    assert "no-such-ref" in err
    assert "--base" in err


def test_a_worktree_packet_includes_untracked_files(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    (repo / "new_parser.py").write_text("def parse():\n    return 1\n")
    (repo / ".gitignore").write_text("ignored.log\n")
    (repo / "ignored.log").write_text("noise\n")
    out = tmp_path / "packet.md"
    result = _run(repo, "--worktree", out=out)
    assert set(result["index"]["files"]) == {"a.txt", "new_parser.py", ".gitignore"}
    text = out.read_text()
    assert "A\tnew_parser.py" in text
    assert "+def parse():" in text
    assert "noise" not in text


def test_untracked_files_alone_make_a_worktree_scope(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "new_parser.py").write_text("x = 1\n")
    result = _run(repo, out=tmp_path / "packet.md")
    assert result["scope"] == "worktree"
    assert "new_parser.py" in result["index"]["files"]


VERIFY_FILE = ".specs/changes/add-foo/.verify/2026-11-17-120000-abc1234/test-output.log"


def test_a_worktree_packet_leaves_out_verify_run_files(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    (repo / VERIFY_FILE).parent.mkdir(parents=True)
    (repo / VERIFY_FILE).write_text("PASSED test_foo\n")
    out = tmp_path / "packet.md"
    result = _run(repo, "--worktree", out=out)
    assert list(result["index"]["files"]) == ["a.txt"]
    assert ".verify" not in out.read_text()


def test_a_staged_packet_leaves_out_verify_run_files(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("changed\n")
    (repo / VERIFY_FILE).parent.mkdir(parents=True)
    (repo / VERIFY_FILE).write_text("PASSED test_foo\n")
    _git(repo, "add", "a.txt", VERIFY_FILE)
    result = _run(repo, "--staged", out=tmp_path / "packet.md")
    assert list(result["index"]["files"]) == ["a.txt"]
    assert result["changed_files"] == 1


def test_a_change_to_verify_run_files_alone_is_no_change(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / VERIFY_FILE).parent.mkdir(parents=True)
    (repo / VERIFY_FILE).write_text("PASSED test_foo\n")
    assert _run(repo, out=tmp_path / "packet.md")["scope"] == "empty"


def test_a_packet_from_a_subdirectory_leaves_out_verify_run_files(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src" / "b.txt").write_text("new\n")
    (repo / VERIFY_FILE).parent.mkdir(parents=True)
    (repo / VERIFY_FILE).write_text("PASSED test_foo\n")
    result = _run(repo / "src", "--worktree", out=tmp_path / "packet.md")
    assert list(result["index"]["files"]) == ["src/b.txt"]


def test_a_branch_packet_leaves_out_verify_run_files(tmp_path):
    repo = _init_repo(tmp_path)
    _git(repo, "checkout", "-qb", "feature")
    (repo / "a.txt").write_text("changed\n")
    (repo / VERIFY_FILE).parent.mkdir(parents=True)
    (repo / VERIFY_FILE).write_text("PASSED test_foo\n")
    _git(repo, "add", "a.txt", VERIFY_FILE)
    _git(repo, "commit", "-qm", "change")
    result = _run(repo, "--base", "main", out=tmp_path / "packet.md")
    assert list(result["index"]["files"]) == ["a.txt"]


def test_a_packet_keeps_a_verify_directory_outside_a_change(tmp_path):
    repo = _init_repo(tmp_path)
    record = repo / ".verify" / "queue-safety" / "alignment.md"
    record.parent.mkdir(parents=True)
    record.write_text("# Alignment\n")
    result = _run(repo, "--worktree", out=tmp_path / "packet.md")
    assert ".verify/queue-safety/alignment.md" in result["index"]["files"]


def _blob(repo: Path, *args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def test_a_staged_packet_records_the_staged_content_of_each_changed_file(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("staged\n")
    _git(repo, "add", "a.txt")
    (repo / "a.txt").write_text("unstaged on top\n")
    result = _run(repo, "--staged", out=tmp_path / "packet.md")
    assert result["content"] == {"a.txt": _blob(repo, "rev-parse", ":a.txt")}


def test_a_worktree_packet_records_the_content_on_disk(tmp_path):
    repo = _init_repo(tmp_path)
    (repo / "a.txt").write_text("on disk\n")
    (repo / "new.txt").write_text("untracked\n")
    result = _run(repo, "--worktree", out=tmp_path / "packet.md")
    assert result["content"] == {name: _blob(repo, "hash-object", name) for name in ("a.txt", "new.txt")}


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks need privileges on Windows")
@pytest.mark.parametrize("target", ["a.txt", "missing.txt"])
def test_a_worktree_packet_records_a_symlink_as_git_stores_it(tmp_path, target):
    repo = _init_repo(tmp_path)
    (repo / "link.txt").symlink_to(target)
    result = _run(repo, "--worktree", out=tmp_path / "packet.md")
    _git(repo, "add", "link.txt")
    assert result["content"]["link.txt"] == _blob(repo, "rev-parse", ":link.txt")


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    raise SystemExit(pytest.main([__file__, "-q", "--rootdir", here, "--confcutdir", here]))
