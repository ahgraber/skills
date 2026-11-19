#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pydantic>=2.7",
#   "pytest>=8",
# ]
# ///
"""Tests for skills/code-review/scripts/review_state.py."""

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "skills" / "code-review" / "scripts" / "review_state.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("review_state", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_state"] = module
    spec.loader.exec_module(module)
    return module


rs = _load_module()


def _git(repo: Path, *args: str, input_text: str | None = None) -> str:
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True, input=input_text
    ).stdout.strip()


def _init_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    # Isolate from the developer's global config (commit signing would fail here).
    _git(repo, "config", "commit.gpgsign", "false")
    (repo / "a.txt").write_text("one\n")
    (repo / "b.txt").write_text("bee\n")
    _git(repo, "add", "a.txt", "b.txt")
    _git(repo, "commit", "-qm", "init")
    return repo


@pytest.fixture
def repo(tmp_path, monkeypatch):
    tmp = tmp_path / "tmp"
    tmp.mkdir()
    monkeypatch.setattr(rs.tempfile, "tempdir", str(tmp))
    repo = _init_repo(tmp_path)
    (repo / ".review").mkdir()
    return repo


def _cli(repo: Path, *argv: str, capsys) -> tuple[int, dict | None, str]:
    code = rs.main([*argv, "--repo", str(repo)])
    out, err = capsys.readouterr()
    return code, (json.loads(out) if out.strip() else None), err


def _ok(repo: Path, *argv: str, capsys) -> dict:
    code, data, err = _cli(repo, *argv, capsys=capsys)
    assert code == 0, err
    return data


def _loc(repo: Path):
    return rs.resolve_locations(repo, None)


def _save(repo: Path, partitions: list[dict]) -> dict:
    return rs.save_list(_loc(repo), rs.ListInput.model_validate({"partitions": partitions}))


def _state(repo: Path) -> dict:
    return json.loads((repo / ".review" / "review-state.json").read_text())


NEW_A = {
    "partition_id": "new-1",
    "feature": "values of a",
    "origin": "spec: a",
    "input_forms": ["empty value"],
    "paths": ["a.txt"],
}
NEW_B = {
    "partition_id": "new-2",
    "feature": "values of b",
    "origin": "spec: b",
    "input_forms": ["empty value"],
    "paths": ["b.txt"],
}


def _snapshot(repo: Path, pid: str):
    state = rs.read_state(_loc(repo).state_path)
    return rs.take_snapshot(_loc(repo), rs._find(state, pid))


def _statuses(checked: list[str], unchecked: tuple[str, ...] = ()) -> list:
    return [rs.InputFormStatus(input_form=f, status="handled") for f in checked] + [
        rs.InputFormStatus(input_form=f, status="not checked") for f in unchecked
    ]


def _inspect(repo: Path, pid: str, scope: str, forms: list[str]) -> bool:
    return rs.record_inspection(_loc(repo), pid, _snapshot(repo, pid), scope, _statuses(forms))


def _pending(repo: Path, scope: str, capsys) -> dict[str, list[str]]:
    data = _ok(repo, "status", "--scope", scope, capsys=capsys)
    return {item["partition_id"]: item["reasons"] for item in data["pending"]["inspect"]}


# --- locations ---------------------------------------------------------------


def test_status_uses_the_main_worktree_review_dir(repo, capsys):
    data = _ok(repo, "status", "--scope", "branch", capsys=capsys)
    assert data["review_dir"] == str((repo / ".review").resolve())
    assert data["review_dir_in_repo"] is True
    assert data["state_exists"] is False
    assert data["pending"]["inspect"] == []


def test_without_review_dir_the_state_goes_under_tmpdir_keyed_by_repo(repo, capsys):
    (repo / ".review").rmdir()
    data = _ok(repo, "status", "--scope", "branch", capsys=capsys)
    review_dir = Path(data["review_dir"])
    assert review_dir.is_relative_to(Path(rs.tempfile.gettempdir()).resolve())
    assert review_dir.name.startswith("repo-")
    assert data["review_dir_in_repo"] is False


def test_a_linked_worktree_shares_the_main_worktree_state(repo, tmp_path, capsys):
    _save(repo, [NEW_A])
    linked = tmp_path / "linked"
    _git(repo, "worktree", "add", "-q", "-b", "feature", str(linked))
    data = _ok(linked, "status", "--scope", "branch", capsys=capsys)
    assert data["review_dir"] == str((repo / ".review").resolve())
    assert data["state_exists"] is True
    assert [p["partition_id"] for p in data["pending"]["inspect"]] == ["P1"]


def test_an_explicit_review_dir_wins(repo, tmp_path, capsys):
    target = tmp_path / "elsewhere"
    data = _ok(repo, "status", "--scope", "branch", "--review-dir", str(target), capsys=capsys)
    assert data["review_dir"] == str(target.resolve())


def test_status_without_a_scope_or_a_review_names_both(repo, capsys):
    code, _, err = _cli(repo, "status", capsys=capsys)
    assert code == 1
    assert "--scope" in err
    assert "--review" in err


# --- saving the partition list ------------------------------------------------------


def test_saving_a_list_assigns_ids_to_new_partitions(repo):
    first = _save(repo, [NEW_A, NEW_B])
    assert first["added"] == ["P1", "P2"]
    assert first["id_map"] == {"new-1": "P1", "new-2": "P2"}
    second = _save(repo, [{**NEW_A, "partition_id": "new-1", "feature": "values of c"}])
    assert second["id_map"] == {"new-1": "P3"}


def test_a_new_partition_naming_an_existing_feature_merges_into_it(repo):
    _save(repo, [NEW_A])
    again = _save(repo, [{**NEW_A, "feature": "Values of A ", "input_forms": ["value given twice"]}])
    assert again["id_map"] == {"new-1": "P1"}
    assert len(_state(repo)["partitions"]) == 1
    assert _state(repo)["partitions"][0]["input_forms"] == ["empty value", "value given twice"]


def test_saving_a_list_merges_into_existing_partitions_without_dropping(repo):
    _save(repo, [NEW_A, NEW_B])
    changed = {**NEW_A, "partition_id": "P1", "input_forms": ["value given twice"], "paths": ["c.txt"]}
    second = _save(repo, [changed])
    assert second["updated"] == ["P1"]
    by_id = {p["partition_id"]: p for p in _state(repo)["partitions"]}
    assert set(by_id) == {"P1", "P2"}
    assert by_id["P1"]["input_forms"] == ["empty value", "value given twice"]
    assert by_id["P1"]["paths"] == ["a.txt", "c.txt"]


def test_saving_a_list_rejects_an_id_it_never_assigned(repo):
    with pytest.raises(rs.ReviewStateError) as exc:
        _save(repo, [{**NEW_A, "partition_id": "P31"}])
    assert "P31" in str(exc.value)
    assert "new-" in str(exc.value)


def test_saving_a_list_maps_child_ids_to_assigned_ids(repo):
    _save(repo, [NEW_A])
    pieces = [
        {"partition_id": "P1", "feature": "values of a", "child_ids": ["new-1", "new-2"]},
        {"partition_id": "new-1", "feature": "empty values of a", "paths": ["a.txt"]},
        {"partition_id": "new-2", "feature": "repeated values of a", "paths": ["a.txt"]},
    ]
    _save(repo, pieces)
    by_id = {p["partition_id"]: p for p in _state(repo)["partitions"]}
    assert by_id["P1"]["child_ids"] == ["P2", "P3"]


def test_saving_a_list_normalizes_paths_to_repo_relative(repo):
    _save(repo, [{**NEW_A, "paths": [str(repo / "a.txt"), "./b.txt"]}])
    assert _state(repo)["partitions"][0]["paths"] == ["a.txt", "b.txt"]


def test_saving_a_list_rejects_a_path_outside_the_repository(repo):
    with pytest.raises(rs.ReviewStateError) as exc:
        _save(repo, [{**NEW_A, "paths": ["../outside.txt"]}])
    assert "outside" in str(exc.value)


@pytest.mark.parametrize("root", [".", "./", ""])
def test_saving_a_list_names_the_repository_root_as_the_problem(repo, root):
    with pytest.raises(rs.ReviewStateError) as exc:
        _save(repo, [{**NEW_A, "paths": [root]}])
    assert "outside" not in str(exc.value)
    assert "repository root" in str(exc.value)


def test_a_malformed_list_names_the_field():
    with pytest.raises(rs.ValidationError) as exc:
        rs.ListInput.model_validate({"partitions": [{"feature": "no id"}]})
    assert "partition_id" in str(exc.value)


# --- inspections and status -------------------------------------------------


def test_a_never_inspected_partition_needs_inspecting(repo, capsys):
    _save(repo, [NEW_A])
    assert _pending(repo, "branch", capsys) == {"P1": ["never inspected"]}


def test_a_staged_inspection_still_counts_after_committing_what_was_inspected(repo, capsys):
    _save(repo, [NEW_A])
    (repo / "a.txt").write_text("staged\n")
    _git(repo, "add", "a.txt")
    _inspect(repo, "P1", "staged", ["empty value"])
    assert _pending(repo, "staged", capsys) == {}
    _git(repo, "commit", "-qm", "commit what was reviewed")
    assert _pending(repo, "branch", capsys) == {}


def test_a_staged_review_of_a_dirty_file_does_not_certify_the_index(repo, capsys):
    _save(repo, [NEW_A])
    (repo / "a.txt").write_text("staged\n")
    _git(repo, "add", "a.txt")
    (repo / "a.txt").write_text("on disk, not staged\n")
    _inspect(repo, "P1", "staged", ["empty value"])
    assert _pending(repo, "staged", capsys) == {"P1": ["files changed"]}


def test_content_changed_after_dispatch_is_not_recorded_as_inspected(repo, capsys):
    _save(repo, [NEW_A])
    snapshot = _snapshot(repo, "P1")
    (repo / "a.txt").write_text("edited while the inspector ran\n")
    rs.record_inspection(_loc(repo), "P1", snapshot, "worktree", _statuses(["empty value"]))
    assert _pending(repo, "worktree", capsys) == {"P1": ["files changed"]}


def test_overlapping_inspections_of_one_partition_keep_their_own_content(repo):
    _save(repo, [NEW_A])
    first = _snapshot(repo, "P1")
    (repo / "a.txt").write_text("second review's content\n")
    second = _snapshot(repo, "P1")
    rs.record_inspection(_loc(repo), "P1", first, "worktree", _statuses(["empty value"]))
    rs.record_inspection(_loc(repo), "P1", second, "worktree", _statuses(["empty value"]))
    inspections = _state(repo)["partitions"][0]["inspections"]
    assert [e["file_hashes"]["a.txt"] for e in inspections] == [
        _git(repo, "hash-object", "--stdin", input_text="one\n"),
        _git(repo, "hash-object", "a.txt"),
    ]


def test_a_snapshot_writes_nothing_to_the_state(repo):
    _save(repo, [NEW_A])
    before = (repo / ".review" / "review-state.json").read_bytes()
    snapshot = _snapshot(repo, "P1")
    assert snapshot.file_hashes == {"a.txt": _git(repo, "hash-object", "a.txt")}
    assert (repo / ".review" / "review-state.json").read_bytes() == before


def test_a_file_changed_after_inspection_needs_inspecting(repo, capsys):
    _save(repo, [NEW_A, NEW_B])
    _inspect(repo, "P1", "branch", ["empty value"])
    _inspect(repo, "P2", "branch", ["empty value"])
    (repo / "a.txt").write_text("edited\n")
    _git(repo, "commit", "-qam", "edit a")
    assert _pending(repo, "branch", capsys) == {"P1": ["files changed"]}


def test_a_worktree_inspection_compares_working_tree_content(repo, capsys):
    _save(repo, [NEW_A])
    (repo / "a.txt").write_text("unstaged\n")
    _inspect(repo, "P1", "worktree", ["empty value"])
    assert _pending(repo, "worktree", capsys) == {}
    assert _pending(repo, "branch", capsys) == {"P1": ["files changed"]}


def test_returning_to_earlier_content_is_recorded(repo, capsys):
    _save(repo, [NEW_A])
    _inspect(repo, "P1", "worktree", ["empty value"])
    (repo / "a.txt").write_text("second\n")
    _inspect(repo, "P1", "worktree", ["empty value"])
    (repo / "a.txt").write_text("one\n")
    assert _inspect(repo, "P1", "worktree", ["empty value"]) is True
    assert _pending(repo, "worktree", capsys) == {}


def test_recording_the_same_inspection_twice_adds_one_entry(repo):
    _save(repo, [NEW_A])
    assert _inspect(repo, "P1", "branch", ["empty value"]) is True
    assert _inspect(repo, "P1", "branch", ["empty value"]) is False
    assert len(_state(repo)["partitions"][0]["inspections"]) == 1


def test_an_inspection_keeps_each_forms_status(repo):
    _save(repo, [{**NEW_A, "input_forms": ["empty value", "value given twice"]}])
    snapshot = _snapshot(repo, "P1")
    rs.record_inspection(_loc(repo), "P1", snapshot, "branch", _statuses(["empty value"], ("value given twice",)))
    assert _state(repo)["partitions"][0]["inspections"][0]["input_forms"] == [
        {"input_form": "empty value", "status": "handled"},
        {"input_form": "value given twice", "status": "not checked"},
    ]


def test_a_form_no_inspection_checked_needs_inspecting(repo, capsys):
    _save(repo, [NEW_A])
    _inspect(repo, "P1", "branch", ["empty value"])
    _save(repo, [{**NEW_A, "partition_id": "P1", "input_forms": ["value given twice"]}])
    assert _pending(repo, "branch", capsys) == {"P1": ["unchecked input forms"]}


def test_a_form_checked_by_an_earlier_inspection_counts(repo, capsys):
    _save(repo, [{**NEW_A, "input_forms": ["empty value", "value given twice"]}])
    _inspect(repo, "P1", "branch", ["empty value", "value given twice"])
    _inspect(repo, "P1", "branch", ["empty value"])
    assert _pending(repo, "branch", capsys) == {}


def _inspect_on_new_content_checking_one_form(repo: Path) -> None:
    _save(repo, [{**NEW_A, "input_forms": ["empty value", "value given twice"]}])
    _inspect(repo, "P1", "worktree", ["empty value", "value given twice"])
    (repo / "a.txt").write_text("version 3\n")
    statuses = _statuses(["empty value"], ("value given twice",))
    rs.record_inspection(_loc(repo), "P1", _snapshot(repo, "P1"), "worktree", statuses)


def test_a_form_checked_only_on_earlier_content_needs_checking_again(repo, capsys):
    _inspect_on_new_content_checking_one_form(repo)
    assert _pending(repo, "worktree", capsys) == {"P1": ["unchecked input forms"]}
    assert _pending_forms(repo, "worktree", capsys) == {"P1": ["value given twice"]}


def test_a_split_piece_does_not_inherit_coverage_of_earlier_content(repo, capsys):
    _inspect_on_new_content_checking_one_form(repo)
    pieces = [
        {"partition_id": "P1", "feature": "values of a", "child_ids": ["new-1", "new-2"]},
        {"partition_id": "new-1", "feature": "empty values of a", "input_forms": ["empty value"], "paths": ["a.txt"]},
        {
            "partition_id": "new-2",
            "feature": "repeated values of a",
            "input_forms": ["value given twice"],
            "paths": ["a.txt"],
        },
    ]
    _save(repo, pieces)
    assert _pending_forms(repo, "worktree", capsys) == {"P3": ["value given twice"]}


def test_a_partition_without_paths_needs_inspecting(repo, capsys):
    _save(repo, [{**NEW_A, "paths": []}])
    _inspect(repo, "P1", "branch", ["empty value"])
    assert _pending(repo, "branch", capsys) == {"P1": ["no paths recorded"]}


def test_an_unknown_partition_names_the_known_ids(repo):
    _save(repo, [NEW_A, NEW_B])
    with pytest.raises(rs.ReviewStateError) as exc:
        _snapshot(repo, "P9")
    assert "P1" in str(exc.value)
    assert "P2" in str(exc.value)


def _pending_forms(repo: Path, scope: str, capsys) -> dict[str, list[str]]:
    data = _ok(repo, "status", "--scope", scope, capsys=capsys)
    return {item["partition_id"]: item["pending_input_forms"] for item in data["pending"]["inspect"]}


def test_a_never_inspected_partition_checks_every_form(repo, capsys):
    _save(repo, [{**NEW_A, "input_forms": ["empty value", "value given twice"]}])
    assert _pending_forms(repo, "branch", capsys) == {"P1": ["empty value", "value given twice"]}


def test_a_reopened_partition_checks_only_its_unchecked_forms(repo, capsys):
    _save(repo, [NEW_A])
    _inspect(repo, "P1", "branch", ["empty value"])
    _save(repo, [{**NEW_A, "partition_id": "P1", "input_forms": ["value given twice"]}])
    assert _pending_forms(repo, "branch", capsys) == {"P1": ["value given twice"]}


def test_a_partition_whose_files_changed_checks_every_form(repo, capsys):
    _save(repo, [NEW_A])
    _inspect(repo, "P1", "branch", ["empty value"])
    _save(repo, [{**NEW_A, "partition_id": "P1", "input_forms": ["value given twice"]}])
    (repo / "a.txt").write_text("edited\n")
    _git(repo, "commit", "-qam", "edit a")
    assert _pending_forms(repo, "branch", capsys) == {"P1": ["empty value", "value given twice"]}


def test_split_pieces_inherit_their_parents_inspections(repo, capsys):
    _save(repo, [{**NEW_A, "input_forms": ["empty value", "value given twice"]}])
    _inspect(repo, "P1", "branch", ["empty value", "value given twice"])
    pieces = [
        {"partition_id": "P1", "feature": "values of a", "child_ids": ["new-1", "new-2"]},
        {"partition_id": "new-1", "feature": "empty values of a", "input_forms": ["empty value"], "paths": ["a.txt"]},
        {
            "partition_id": "new-2",
            "feature": "repeated values of a",
            "input_forms": ["value given twice"],
            "paths": ["a.txt"],
        },
    ]
    _save(repo, pieces)
    assert _pending(repo, "branch", capsys) == {}


def test_a_split_piece_checks_forms_its_parent_never_checked(repo, capsys):
    _save(repo, [NEW_A])
    _inspect(repo, "P1", "branch", ["empty value"])
    pieces = [
        {"partition_id": "P1", "feature": "values of a", "child_ids": ["new-1"]},
        {
            "partition_id": "new-1",
            "feature": "empty values of a",
            "input_forms": ["empty value", "a lone space"],
            "paths": ["a.txt"],
        },
    ]
    _save(repo, pieces)
    assert _pending_forms(repo, "branch", capsys) == {"P2": ["a lone space"]}


def test_a_split_partition_is_not_inspected(repo, capsys):
    _save(repo, [NEW_A])
    _save(
        repo,
        [{"partition_id": "P1", "feature": "values of a", "child_ids": ["new-1"]}, {**NEW_B, "partition_id": "new-1"}],
    )
    assert _pending(repo, "branch", capsys) == {"P2": ["never inspected"]}


# --- path handling -----------------------------------------------------------------


def test_a_path_that_looks_like_a_pattern_is_literal(repo, capsys):
    (repo / "[ab].txt").write_text("brackets\n")
    _git(repo, "add", "[ab].txt")
    _git(repo, "commit", "-qm", "brackets")
    _save(repo, [{**NEW_A, "paths": ["[ab].txt"]}])
    _inspect(repo, "P1", "staged", ["empty value"])
    (repo / "a.txt").write_text("unrelated\n")
    _git(repo, "add", "a.txt")
    assert _pending(repo, "staged", capsys) == {}
    assert _state(repo)["partitions"][0]["paths"] == ["[ab].txt"]


def test_a_file_name_with_a_newline_is_hashed(repo, capsys):
    name = "line\nname.txt"
    (repo / name).write_text("x\n")
    _save(repo, [{**NEW_A, "paths": [name]}])
    _inspect(repo, "P1", "worktree", ["empty value"])
    assert _pending(repo, "worktree", capsys) == {}
    (repo / name).write_text("y\n")
    assert _pending(repo, "worktree", capsys) == {"P1": ["files changed"]}


@pytest.mark.skipif(sys.platform == "win32", reason="symlinks need privileges on Windows")
def test_a_symlink_is_identified_by_its_link_text(repo, capsys):
    (repo / "link").symlink_to("missing-one")
    (repo / "live").symlink_to("a.txt")
    _git(repo, "add", "link", "live")
    _save(repo, [{**NEW_A, "paths": ["link", "live"]}])
    _inspect(repo, "P1", "worktree", ["empty value"])
    assert _pending(repo, "staged", capsys) == {}
    (repo / "link").unlink()
    (repo / "link").symlink_to("missing-two")
    assert _pending(repo, "worktree", capsys) == {"P1": ["files changed"]}


# --- finished reviews -----------------------------------------------------------------


def _finished(repo: Path, report: str, review_id: str = "20261030-000000-abc1234") -> bool:
    _, branch = rs.head_and_branch(repo)
    entry = rs.FinishedReview(
        review_id=review_id, head="abc1234", branch=branch, date="2026-10-30", report=report, scope="branch"
    )
    return rs.record_finished_review(_loc(repo), entry)


def test_status_reports_the_previous_review_on_this_branch(repo, capsys):
    report = repo / ".review" / "code-review-1.md"
    report.write_text("# report\n")
    _finished(repo, str(report))
    data = _ok(repo, "status", "--scope", "branch", capsys=capsys)
    assert data["previous_review"]["report"] == str(report)
    assert data["previous_review"]["report_exists"] is True
    _git(repo, "checkout", "-qb", "other")
    assert _ok(repo, "status", "--scope", "branch", capsys=capsys)["previous_review"] is None


def test_a_detached_head_has_no_previous_review(repo, capsys):
    _git(repo, "checkout", "-q", "--detach")
    _finished(repo, str(repo / ".review" / "r.md"))
    assert _ok(repo, "status", "--scope", "branch", capsys=capsys)["previous_review"] is None


def test_recording_the_same_finished_review_twice_adds_one_entry(repo):
    report = str(repo / ".review" / "r.md")
    assert _finished(repo, report) is True
    assert _finished(repo, report) is False
    assert len(_state(repo)["reviews"]) == 1


# --- state file -----------------------------------------------------------------


def test_a_state_file_of_an_earlier_version_is_refused(repo, capsys):
    v4 = {"version": 4, "repo": "repo", "partitions": [], "runs": []}
    (repo / ".review" / "review-state.json").write_text(json.dumps(v4))
    code, _, err = _cli(repo, "status", "--scope", "branch", capsys=capsys)
    assert code == 1
    assert "- version:" in err
    assert "move it aside" in err


def test_an_invalid_state_file_is_an_error_not_a_fresh_start(repo, capsys):
    (repo / ".review" / "review-state.json").write_text("{not json")
    code, _, err = _cli(repo, "status", "--scope", "branch", capsys=capsys)
    assert code == 1
    assert "review-state.json" in err


def test_an_invalid_scope_names_the_valid_set(repo, capsys):
    with pytest.raises(SystemExit) as exc:
        rs.main(["status", "--scope", "everything", "--repo", str(repo)])
    assert exc.value.code == 2
    assert "staged" in capsys.readouterr().err


# --- concurrency -------------------------------------------------------------------

SAVER = """
import importlib.util, sys
spec = importlib.util.spec_from_file_location("review_state", sys.argv[1])
rs = importlib.util.module_from_spec(spec)
sys.modules["review_state"] = rs
spec.loader.exec_module(rs)
item = {"partition_id": "new-1", "feature": sys.argv[3], "paths": ["a.txt"]}
rs.save_list(rs.resolve_locations(rs.Path(sys.argv[2]), None), rs.ListInput.model_validate({"partitions": [item]}))
"""


def test_parallel_writers_lose_no_update(repo, tmp_path):
    saver = tmp_path / "saver.py"
    saver.write_text(SAVER)
    env = {**os.environ, "TMPDIR": rs.tempfile.gettempdir()}
    procs = [
        subprocess.Popen(  # noqa: S603
            [sys.executable, str(saver), str(SCRIPT), str(repo), f"feature {i}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        for i in range(12)
    ]
    for proc in procs:
        _, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, err
    features = sorted(p["feature"] for p in _state(repo)["partitions"])
    assert features == sorted(f"feature {i}" for i in range(12))


@pytest.mark.skipif(sys.platform == "win32", reason="the test holds the lock with fcntl")
def test_a_held_lock_times_out_with_its_path(repo, monkeypatch):
    import fcntl

    _save(repo, [NEW_A])
    monkeypatch.setattr(rs, "LOCK_TIMEOUT_SECONDS", 0.3)
    lock = repo / ".review" / "review-state.json.lock"
    with lock.open("a+") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        with pytest.raises(rs.ReviewStateError) as exc:
            _save(repo, [NEW_B])
    assert str(lock) in str(exc.value)


def test_a_lock_file_left_by_a_crashed_writer_does_not_block(repo):
    _save(repo, [NEW_A])
    lock = repo / ".review" / "review-state.json.lock"
    lock.write_text("left behind\n")
    _inspect(repo, "P1", "branch", ["empty value"])
    assert len(_state(repo)["partitions"][0]["inspections"]) == 1


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    raise SystemExit(pytest.main([__file__, "-q", "--rootdir", here, "--confcutdir", here]))
