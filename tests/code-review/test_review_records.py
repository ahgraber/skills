#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pydantic>=2.7",
#   "pytest>=8",
# ]
# ///
"""Tests for the review records in skills/code-review/scripts/review_state.py."""

import importlib.util
import json
import os
from pathlib import Path
import shlex
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

SECTIONS = {
    "Metadata": [3, 9],
    "Changed files (name-status)": [11, 15],
    "Diff": [17, 60],
    "Source of truth": [62, 100],
}
FILES = {"a.txt": [19, 38], "b.txt": [39, 59]}
FORMS = ["empty value", "value given twice"]
TEXT_VALUES = ("--intent", "reject empty values", "--how-to-run", "uv run pytest tests/")
VALUES = (*TEXT_VALUES, "--depth", "deep")


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(  # noqa: S603
        ["git", "-C", str(repo), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


@pytest.fixture
def repo(tmp_path, monkeypatch):
    tmp = tmp_path / "tmp"
    tmp.mkdir()
    monkeypatch.setattr(rs.tempfile, "tempdir", str(tmp))
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "commit.gpgsign", "false")
    for name in ("a.txt", "b.txt", "c.txt"):
        (repo / name).write_text(f"{name}\n")
    _git(repo, "add", ".")
    _git(repo, "commit", "-qm", "init")
    (repo / "a.txt").write_text("changed a\n")
    (repo / "b.txt").write_text("changed b\n")
    _git(repo, "add", "a.txt", "b.txt")
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


def _packet_json(repo: Path, tmp_path: Path, **overrides) -> Path:
    packet = tmp_path / "packet.md"
    packet.write_text("\n".join(f"line {n}" for n in range(1, 101)) + "\n")
    info = {
        "packet_path": str(packet),
        "index": {"sections": SECTIONS, "files": FILES},
        "scope": "staged",
        "head": _git(repo, "rev-parse", "HEAD"),
        "branch": "main",
        "diff_truncated": False,
        "has_source_of_truth": True,
    } | overrides
    path = tmp_path / "packet.json"
    path.write_text(json.dumps(info))
    return path


def _save(repo: Path, partitions: list[dict]) -> dict:
    return rs.save_list(rs.resolve_locations(repo, None), rs.ListInput.model_validate({"partitions": partitions}))


@pytest.fixture
def work(repo, tmp_path, capsys) -> Path:
    _save(
        repo,
        [
            {
                "partition_id": "new-1",
                "feature": "values of a",
                "origin": "spec",
                "input_forms": FORMS,
                "paths": ["a.txt"],
            },
            {
                "partition_id": "new-2",
                "feature": "values of b",
                "origin": "spec",
                "input_forms": FORMS,
                "paths": ["b.txt"],
            },
        ],
    )
    return _start(repo, tmp_path, capsys, "--passed-checks", "uv run pytest", "prek run --all-files")


def _start(repo: Path, tmp_path: Path, capsys, *extra: str, **packet) -> Path:
    path = str(_packet_json(repo, tmp_path, **packet))
    data = _ok(repo, "start-review", "--scope", "staged", "--packet-json", path, *extra, *VALUES, capsys=capsys)
    return Path(data["path"])


def _update(repo: Path, work: Path, *flags: str, capsys) -> dict:
    return _ok(repo, "update-review", "--review", work.name, *flags, capsys=capsys)


def _dispatch(repo: Path, work: Path, role: str, *extra: str, capsys) -> dict:
    """Register one dispatch; return its entry with what the script stored and wrote for it."""
    data = _ok(repo, "dispatch", role, "--review", work.name, *extra, capsys=capsys)
    (entry,) = data["dispatches"]
    stored = _review_dispatch(work, entry["dispatch_id"])
    written = json.loads(Path(stored["input_path"]).read_text())
    return {
        "dispatch_id": entry["dispatch_id"],
        "role": entry["role"],
        "input_path": stored["input_path"],
        "output_path": stored["output_path"],
        "submit_command": written["submit_command"],
        "packet_ranges": stored["packet_ranges"],
        "prompt_path": entry["prompt_path"],
        "already_dispatched": data["already_dispatched"],
    }


def _review_dispatch(work: Path, dispatch_id: str) -> dict:
    stored = json.loads((work / "review.json").read_text())["dispatches"]
    return next(d for d in stored if d["dispatch_id"] == dispatch_id)


def _submit(repo: Path, work: Path, d: dict, output: dict | str, capsys) -> tuple[int, dict | None, str]:
    Path(d["output_path"]).write_text(output if isinstance(output, str) else json.dumps(output))
    return _cli(repo, "submit", d["dispatch_id"], "--review", work.name, capsys=capsys)


def _submitted(repo: Path, work: Path, d: dict, output: dict | str, capsys) -> dict:
    code, data, err = _submit(repo, work, d, output, capsys)
    assert code == 0, err
    return data


def _status(repo: Path, work: Path, capsys) -> dict:
    return _ok(repo, "status", "--review", work.name, capsys=capsys)


def _pending(repo: Path, work: Path, capsys) -> dict:
    return _status(repo, work, capsys)["pending"]


def _input(d: dict) -> dict:
    return json.loads(Path(d["input_path"]).read_text())


def claim(**kw) -> dict:
    base = {
        "site": "a.txt:1",
        "input_form": "empty value",
        "input": "''",
        "expected": "an error",
        "source": "spec: values",
        "predicted": "accepted",
        "observation": "an empty value is accepted",
        "direction": "reject it",
        "priority": "high",
        "reachable": "yes",
        "introduced": "this change",
        "failure_mode": {"name": "empty values", "description": "an empty value reaches the parser with no check"},
    }
    return base | kw


def run(verdict: str = "confirmed", **kw) -> dict:
    base = {"command": "uv run probe.py", "output": "ok", "probe_path": "probe.py", "reached_path": True}
    return base | {"verdict": verdict} | kw


def inspector_output(forms: list[str], claims: list[dict], **kw) -> dict:
    statuses = [{"input_form": f, "status": "claims" if claims else "handled"} for f in forms]
    return {
        "read_through": 100,
        "files_read": ["a.txt"],
        "input_forms": statuses,
        "claims": claims,
        "result": "claims" if claims else "handled",
    } | kw


def too_coarse_output(**kw) -> dict:
    return {
        "read_through": 100,
        "input_forms": [
            {"input_form": FORMS[0], "status": "handled"},
            {"input_form": FORMS[1], "status": "not checked"},
        ],
        "result": "too coarse",
        "proposed_split": "by value kind",
    } | kw


def _inspect(repo, work, pid: str, claims: list[dict], capsys) -> dict:
    d = _dispatch(repo, work, "inspector", "--partition", pid, capsys=capsys)
    return _submitted(repo, work, d, inspector_output(_input(d)["pending_input_forms"], claims), capsys)


def mode(name: str, *record_ids: str) -> dict:
    return {"name": name, "description": f"how {name} fails", "record_ids": list(record_ids)}


def _consolidate(repo, work, capsys, duplicates=(), failure_modes=None) -> dict:
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    ids = [r["record_id"] for r in _input(d)["records"]]
    dup_ids = {x["record_id"] for x in duplicates}
    if failure_modes is None:
        failure_modes = [mode(f"mode {i}", i) for i in ids if i not in dup_ids]
    return _submitted(repo, work, d, {"duplicates": list(duplicates), "failure_modes": failure_modes}, capsys)


def _run_all(repo, work, capsys, verdicts: dict[str, str] | None = None) -> dict:
    d = _dispatch(repo, work, "runner", capsys=capsys)
    ids = [r["record_id"] for r in _input(d)["records"]]
    results = []
    for i in ids:
        verdict = (verdicts or {}).get(i, "confirmed")
        extra = {"reason": "needs a live service", "reached_path": False} if verdict == "not runnable" else {}
        results.append({"record_id": i, **run(verdict, **extra)})
    return _submitted(repo, work, d, {"results": results}, capsys)


def _review(work: Path) -> dict:
    return json.loads((work / "review.json").read_text())


def _records(work: Path) -> dict[str, dict]:
    return {r["record_id"]: r for r in _review(work)["records"]}


def _verdict(work: Path, record: dict) -> str | None:
    return rs.verdict(rs.read_review(work), rs.Record.model_validate(record))


def _round_one_lenses(repo, work, capsys) -> None:
    """Dispatch and submit each round-one role (the lenses and the test adversary) not dispatched yet."""
    for entry in rs._round_one_missing(rs.read_review(work)):
        role, _, component = entry.partition(" --component ")
        extra = ("--component", component) if component else ()
        _submitted(repo, work, _dispatch(repo, work, role, *extra, capsys=capsys), {"read_through": 100}, capsys)


# --- start-review ---------------------------------------------------------------


def test_a_truncated_packet_is_refused(repo, tmp_path, capsys):
    path = _packet_json(repo, tmp_path, diff_truncated=True)
    code, _, err = _cli(repo, "start-review", "--scope", "staged", "--packet-json", str(path), *VALUES, capsys=capsys)
    assert code == 1
    assert "--max-diff-bytes" in err


def test_a_packet_of_another_scope_is_refused(repo, tmp_path, capsys):
    path = _packet_json(repo, tmp_path, scope="worktree")
    code, _, err = _cli(repo, "start-review", "--scope", "staged", "--packet-json", str(path), *VALUES, capsys=capsys)
    assert code == 1
    assert "worktree" in err


def test_a_staged_review_refuses_a_changed_file_that_differs_on_disk(repo, tmp_path, capsys):
    (repo / "a.txt").write_text("edited after staging\n")
    path = str(_packet_json(repo, tmp_path))
    code, _, err = _cli(repo, "start-review", "--scope", "staged", "--packet-json", path, *VALUES, capsys=capsys)
    assert code == 1
    assert "a.txt" in err
    assert "b.txt" not in err
    assert "git stash --keep-index" in err
    assert "--worktree" in err


def test_an_inspector_is_not_dispatched_on_files_that_differ_on_disk(repo, work, capsys):
    (repo / "a.txt").write_text("edited during the review\n")
    code, _, err = _cli(repo, "dispatch", "inspector", "--review", work.name, "--partition", "P1", capsys=capsys)
    assert code == 1
    assert "a.txt" in err
    assert not [d for d in _review(work)["dispatches"] if d["role"] == "inspector"]


@pytest.mark.parametrize("role", ["quality-lens", "security-lens", "test-adversary", "hunter", "runner"])
def test_a_role_that_reads_or_runs_the_files_is_not_dispatched_when_a_reviewed_file_differs_on_disk(
    repo, work, capsys, role
):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys)
    if role == "hunter":
        _run_all(repo, work, capsys)
    (repo / "b.txt").write_text("edited during the review\n")
    extra = ("--failure-mode", "mode R1-1") if role == "hunter" else ()
    code, _, err = _cli(repo, "dispatch", role, "--review", work.name, *extra, capsys=capsys)
    assert code == 1
    assert "b.txt" in err
    assert not [d for d in _review(work)["dispatches"] if d["role"] == role]


def test_a_role_that_reads_only_records_is_dispatched_when_a_reviewed_file_differs_on_disk(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    (repo / "b.txt").write_text("edited during the review\n")
    assert _dispatch(repo, work, "consolidator", capsys=capsys)["role"] == "consolidator"


def _branch_work(repo: Path, tmp_path: Path, capsys) -> Path:
    """Commit the staged change, save a partition for each changed file, and start a branch review of the commit."""
    _git(repo, "commit", "-qm", "change a and b")
    _save(
        repo,
        [
            {"partition_id": f"new-{n}", "feature": f"values of {name}", "origin": "spec", "input_forms": FORMS}
            | {"paths": [f"{name}.txt"]}
            for n, name in enumerate(("a", "b"), start=1)
        ],
    )
    path = str(_packet_json(repo, tmp_path, scope="branch"))
    data = _ok(repo, "start-review", "--scope", "branch", "--packet-json", path, *VALUES, capsys=capsys)
    return Path(data["path"])


def _commit_edit(repo: Path, name: str) -> None:
    (repo / name).write_text("changed by a later commit\n")
    _git(repo, "commit", "-qam", f"edit {name}")


def test_a_branch_review_keeps_its_inspections_when_the_branch_gets_a_later_commit(repo, tmp_path, capsys):
    work = _branch_work(repo, tmp_path, capsys)
    _inspect(repo, work, "P1", [], capsys)
    _commit_edit(repo, "a.txt")
    status = _status(repo, work, capsys)
    assert [p["partition_id"] for p in status["pending"]["inspect"]] == ["P2"]
    assert status["head"] == _review(work)["head"]


def test_a_branch_review_dispatches_no_inspector_on_a_file_that_a_later_commit_changed(repo, tmp_path, capsys):
    work = _branch_work(repo, tmp_path, capsys)
    reviewed = _review(work)["head"]
    _commit_edit(repo, "a.txt")
    code, _, err = _cli(repo, "dispatch", "inspector", "--review", work.name, "--partition", "P1", capsys=capsys)
    assert code == 1
    assert "a.txt" in err
    assert reviewed[:7] in err
    assert "HEAD" not in err
    assert "--repo" in err


def test_a_branch_review_goes_on_in_a_separate_checkout_of_its_commit(repo, tmp_path, capsys):
    work = _branch_work(repo, tmp_path, capsys)
    checkout = tmp_path / "checkout"
    _git(repo, "worktree", "add", "-q", "--detach", str(checkout), _review(work)["head"])
    _commit_edit(repo, "a.txt")
    d = _dispatch(checkout, work, "inspector", "--partition", "P1", capsys=capsys)
    assert _input(d)["root"] == str(checkout.resolve())


def test_an_open_dispatch_given_again_from_a_separate_checkout_reads_that_checkout(repo, tmp_path, capsys):
    work = _branch_work(repo, tmp_path, capsys)
    _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    checkout = tmp_path / "checkout"
    _git(repo, "worktree", "add", "-q", "--detach", str(checkout), _review(work)["head"])
    _commit_edit(repo, "a.txt")
    again = _dispatch(checkout, work, "inspector", "--partition", "P1", capsys=capsys)
    assert again["already_dispatched"] is True
    data = _input(again)
    assert data["root"] == str(checkout.resolve())
    assert str(checkout.resolve()) in data["submit_command"]


@pytest.mark.parametrize("argv", [("dispatch", "quality-lens"), ("dispatch",)], ids=["with a role", "with no role"])
def test_an_open_dispatch_is_not_given_again_while_a_reviewed_file_differs_on_disk(repo, work, capsys, argv):
    _dispatch(repo, work, "quality-lens", capsys=capsys)
    (repo / "a.txt").write_text("edited after the dispatch\n")
    code, _, err = _cli(repo, *argv, "--review", work.name, capsys=capsys)
    assert code == 1
    assert "a.txt" in err


def test_a_staged_review_refuses_a_packet_built_before_the_staged_files_changed(repo, tmp_path, capsys):
    built = {"a.txt": _git(repo, "rev-parse", ":a.txt"), "b.txt": _git(repo, "rev-parse", ":b.txt")}
    (repo / "a.txt").write_text("staged after the packet\n")
    _git(repo, "add", "a.txt")
    path = str(_packet_json(repo, tmp_path, content=built))
    code, _, err = _cli(repo, "start-review", "--scope", "staged", "--packet-json", path, *VALUES, capsys=capsys)
    assert code == 1
    assert "rebuild the packet" in err
    assert "a.txt" in err


def test_a_review_refuses_a_dispatch_after_the_staged_files_change(repo, tmp_path, capsys):
    built = {"a.txt": _git(repo, "rev-parse", ":a.txt"), "b.txt": _git(repo, "rev-parse", ":b.txt")}
    work = _start(repo, tmp_path, capsys, content=built)
    (repo / "a.txt").write_text("staged during the review\n")
    _git(repo, "add", "a.txt")
    code, _, err = _cli(repo, "dispatch", "quality-lens", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "a.txt" in err


def test_a_branch_review_goes_on_when_a_later_commit_changes_a_file_outside_its_partitions(repo, tmp_path, capsys):
    work = _branch_work(repo, tmp_path, capsys)
    _commit_edit(repo, "c.txt")
    _inspect(repo, work, "P1", [], capsys)
    assert [p["partition_id"] for p in _pending(repo, work, capsys)["inspect"]] == ["P2"]


def test_the_review_id_names_the_start_time_and_the_head(repo, work):
    head = _git(repo, "rev-parse", "HEAD")
    assert work.name.endswith(f"-{head[:7]}")
    assert work.name[:15].replace("-", "").isdigit()
    assert _review(work)["review_id"] == work.name


def test_two_reviews_from_one_commit_in_one_second_get_distinct_ids(repo, tmp_path, monkeypatch, capsys):
    frozen = rs._dt.datetime(2026, 10, 29, 18, 22, 33, tzinfo=rs._dt.UTC)

    class Frozen(rs._dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return frozen

    monkeypatch.setattr(rs._dt, "datetime", Frozen)
    path = str(_packet_json(repo, tmp_path))
    first = _ok(repo, "start-review", "--scope", "staged", "--packet-json", path, *VALUES, capsys=capsys)["review_id"]
    path = str(_packet_json(repo, tmp_path, base="another base"))
    second = _ok(repo, "start-review", "--scope", "staged", "--packet-json", path, *VALUES, capsys=capsys)["review_id"]
    head = _git(repo, "rev-parse", "HEAD")[:7]
    assert first == f"20261029-182233-{head}"
    assert second == f"20261029-182233-{head}-2"


def test_the_review_keeps_its_own_copy_of_the_packet(repo, tmp_path, work, capsys):
    (tmp_path / "packet.md").unlink()
    (tmp_path / "packet.json").unlink()
    d = _dispatch(repo, work, "security-lens", capsys=capsys)
    assert _input(d)["packet"] == str(work / "packet.md")
    assert (work / "packet.md").read_text().startswith("line 1\n")
    assert json.loads((work / "packet.json").read_text())["scope"] == "staged"
    assert _review(work)["packet"]["path"] == str(work / "packet.md")


def test_dispatch_names_a_prompt_path_inside_the_review(repo, work, capsys):
    d = _dispatch(repo, work, "quality-lens", capsys=capsys)
    assert d["prompt_path"] == str(work / "prompts" / f"{d['dispatch_id']}-quality-lens.md")
    assert (work / "prompts").is_dir()


# --- dispatch inputs and packet ranges ------------------------------------------------


def test_an_inspector_gets_its_forms_its_hunks_and_the_source_of_truth(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    data = _input(d)
    assert data["partition_id"] == "P1"
    assert data["feature"] == "values of a"
    assert data["pending_input_forms"] == FORMS
    assert data["packet_ranges"] == [FILES["a.txt"], SECTIONS["Source of truth"]]
    assert f"submit {d['dispatch_id']} --repo" in data["submit_command"]
    assert data["submit_command"].endswith(f"--review {work.name}")


def test_a_list_builder_gets_the_metadata_its_hunks_and_the_source_of_truth(repo, work, capsys):
    d = _dispatch(repo, work, "list-builder", "--component", "a", "--paths", "a.txt", capsys=capsys)
    data = _input(d)
    expected = sorted(
        [SECTIONS["Metadata"], SECTIONS["Changed files (name-status)"], FILES["a.txt"], SECTIONS["Source of truth"]]
    )
    assert data["packet_ranges"] == expected
    assert data["paths"] == ["a.txt"]
    assert {p["feature"] for p in data["partitions"]} == {"values of a", "values of b"}


def test_a_lens_gets_the_whole_packet(repo, work, capsys):
    d = _dispatch(repo, work, "security-lens", capsys=capsys)
    assert _input(d)["packet_ranges"] == [[1, 100]]


def _builders(repo, work, capsys, *components: str) -> None:
    for name in components:
        d = _dispatch(repo, work, "list-builder", "--component", name, "--paths", f"{name}.txt", capsys=capsys)
        _submitted(repo, work, d, {"read_through": 100, "proposals": []}, capsys)


def test_a_quality_lens_for_a_component_reads_the_list_builders_paths(repo, work, capsys):
    _builders(repo, work, capsys, "a", "b")
    d = _dispatch(repo, work, "quality-lens", "--component", "b", capsys=capsys)
    data = _input(d)
    assert data["component"] == "b"
    assert data["paths"] == ["b.txt"]
    expected = sorted(
        [SECTIONS["Metadata"], SECTIONS["Changed files (name-status)"], FILES["b.txt"], SECTIONS["Source of truth"]]
    )
    assert data["packet_ranges"] == expected


def test_a_quality_lens_without_a_component_reads_the_whole_packet(repo, work, capsys):
    _builders(repo, work, capsys, "a", "b")
    d = _dispatch(repo, work, "quality-lens", capsys=capsys)
    assert _input(d)["packet_ranges"] == [[1, 100]]
    assert "component" not in _input(d)


def test_a_quality_lens_for_an_unknown_component_names_the_components(repo, work, capsys):
    _builders(repo, work, capsys, "a", "b")
    code, _, err = _cli(repo, "dispatch", "quality-lens", "--review", work.name, "--component", "c", capsys=capsys)
    assert code == 1
    assert "'a', 'b'" in err


def test_a_quality_lens_takes_its_paths_from_the_list_builder(repo, work, capsys):
    _builders(repo, work, capsys, "a")
    argv = ["dispatch", "quality-lens", "--review", work.name, "--component", "a", "--paths", "b.txt"]
    code, _, err = _cli(repo, *argv, capsys=capsys)
    assert code == 1
    assert "--paths" in err


def test_a_repeated_quality_lens_dispatch_matches_its_component(repo, work, capsys):
    _builders(repo, work, capsys, "a", "b")
    first = _dispatch(repo, work, "quality-lens", "--component", "a", capsys=capsys)
    again = _dispatch(repo, work, "quality-lens", "--component", "a", capsys=capsys)
    other = _dispatch(repo, work, "quality-lens", "--component", "b", capsys=capsys)
    assert again["dispatch_id"] == first["dispatch_id"]
    assert again["already_dispatched"] is True
    assert other["dispatch_id"] != first["dispatch_id"]


def test_each_component_of_a_change_needs_its_own_quality_lens(repo, work, capsys):
    _builders(repo, work, capsys, "a", "b")
    lens = _dispatch(repo, work, "quality-lens", capsys=capsys)
    _submitted(repo, work, lens, {"read_through": 100}, capsys)
    missing = rs._round_one_missing(rs.read_review(work))
    assert missing[:2] == ["quality-lens --component a", "quality-lens --component b"]
    for name in ("a", "b"):
        d = _dispatch(repo, work, "quality-lens", "--component", name, capsys=capsys)
        _submitted(repo, work, d, {"read_through": 100}, capsys)
    assert not [m for m in rs._round_one_missing(rs.read_review(work)) if m.startswith("quality-lens")]


def test_a_change_with_one_component_takes_one_quality_lens(repo, work, capsys):
    _builders(repo, work, capsys, "a")
    lens = _dispatch(repo, work, "quality-lens", capsys=capsys)
    _submitted(repo, work, lens, {"read_through": 100}, capsys)
    assert "quality-lens" not in " ".join(rs._round_one_missing(rs.read_review(work)))


@pytest.mark.parametrize("architecture", ["yes", "no"])
def test_a_change_with_one_component_needs_the_lens_that_reads_the_whole_packet(repo, work, capsys, architecture):
    _update(repo, work, "--architecture", architecture, capsys=capsys)
    _builders(repo, work, capsys, "a")
    _dispatch(repo, work, "quality-lens", "--component", "a", capsys=capsys)
    assert "quality-lens" in rs._round_one_missing(rs.read_review(work))
    _dispatch(repo, work, "quality-lens", capsys=capsys)
    assert "quality-lens" not in rs._round_one_missing(rs.read_review(work))


def test_dispatching_an_open_assignment_again_returns_the_open_dispatch(repo, work, capsys):
    first = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    again = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    assert first["already_dispatched"] is False
    assert again == first | {"already_dispatched": True}
    lens = _dispatch(repo, work, "security-lens", capsys=capsys)
    assert _dispatch(repo, work, "security-lens", capsys=capsys)["dispatch_id"] == lens["dispatch_id"]
    assert len(_review(work)["dispatches"]) == 2


def test_a_runner_dispatched_again_with_nothing_new_returns_the_open_one(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys)
    first = _dispatch(repo, work, "runner", capsys=capsys)
    assert _dispatch(repo, work, "runner", capsys=capsys)["dispatch_id"] == first["dispatch_id"]
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    _consolidate(repo, work, capsys)
    second = _dispatch(repo, work, "runner", capsys=capsys)
    assert second["dispatch_id"] != first["dispatch_id"]
    assert [r["record_id"] for r in _input(second)["records"]] == ["R1-2"]


# --- inspector output ------------------------------------------------------------------------


def test_an_inspector_must_report_every_form(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    code, _, err = _submit(repo, work, d, inspector_output(["empty value"], []), capsys)
    assert code == 1
    assert "value given twice" in err


def test_an_inspector_that_stopped_reading_early_is_sent_back(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    code, _, err = _submit(repo, work, d, inspector_output(FORMS, [], read_through=40), capsys)
    assert code == 1
    assert "line 41 through 100" in err


def test_a_misnamed_field_is_an_error_that_names_it(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    bad = claim()
    bad["expected_result"] = bad.pop("expected")
    code, _, err = _submit(repo, work, d, inspector_output(FORMS, [bad]), capsys)
    assert code == 1
    lines = err.splitlines()
    assert "- claims.0.expected: Field required" in lines
    assert "- claims.0.expected_result: Extra inputs are not permitted" in lines
    assert lines[-1].endswith("schema inspector")


def test_a_claim_needs_a_proposed_failure_mode(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    bad = claim()
    del bad["failure_mode"]
    code, _, err = _submit(repo, work, d, inspector_output(FORMS, [bad]), capsys)
    assert code == 1
    assert "- claims.0.failure_mode: Field required" in err.splitlines()


def test_invalid_json_is_an_error_and_the_dispatch_stays_open(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    code, _, _ = _submit(repo, work, d, "{not json", capsys)
    assert code == 1
    assert _status(repo, work, capsys)["open_dispatches"][0]["dispatch_id"] == d["dispatch_id"]


def test_a_claim_form_must_be_assigned_or_new(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    code, _, err = _submit(repo, work, d, inspector_output(FORMS, [claim(input_form="something else")]), capsys)
    assert code == 1
    assert "new: <form>" in err
    _submitted(repo, work, d, inspector_output(FORMS, [claim(input_form="new: a value of only spaces")]), capsys)


def test_records_get_ids_at_submit_and_count_up_in_the_round(repo, work, capsys):
    first = _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    second = _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    assert first["record_ids"] == ["R1-1", "R1-2"]
    assert second["record_ids"] == ["R1-3"]


def test_submitting_a_recorded_dispatch_again_returns_the_first_result(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    first = _submitted(repo, work, d, inspector_output(FORMS, [claim()]), capsys)
    again = _submitted(repo, work, d, inspector_output(FORMS, [claim()]), capsys)
    assert first["already_submitted"] is False
    assert again == first | {"already_submitted": True}
    assert len(_review(work)["records"]) == 1


def test_a_too_coarse_inspector_records_only_the_forms_it_checked(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    _submitted(repo, work, d, too_coarse_output(), capsys)
    pending = _ok(repo, "status", "--scope", "staged", capsys=capsys)["pending"]["inspect"]
    assert {n["partition_id"]: n["pending_input_forms"] for n in pending}["P1"] == [FORMS[1]]
    assert _pending(repo, work, capsys)["refine"] == [d["dispatch_id"]]


def test_an_inspector_that_checked_no_form_covers_nothing(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    output = too_coarse_output(input_forms=[{"input_form": f, "status": "not checked"} for f in FORMS])
    _submitted(repo, work, d, output, capsys)
    pending = _ok(repo, "status", "--scope", "staged", capsys=capsys)["pending"]["inspect"]
    assert {n["partition_id"]: n["reasons"] for n in pending}["P1"] == ["never inspected"]


def test_an_inspector_dispatch_keeps_its_snapshot_in_the_review(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    stored = next(x for x in _review(work)["dispatches"] if x["dispatch_id"] == d["dispatch_id"])
    assert set(stored["snapshot"]["file_hashes"]) == {"a.txt"}
    state = json.loads((repo / ".review" / "review-state.json").read_text())
    assert all("pending" not in p for p in state["partitions"])


def test_unchecked_forms_need_a_too_coarse_result(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    output = inspector_output(FORMS, [])
    output["input_forms"][1]["status"] = "not checked"
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "too coarse" in err


def test_an_inspector_with_no_form_to_check_is_refused(repo, work, capsys):
    _inspect(repo, work, "P1", [], capsys)
    code, _, err = _cli(repo, "dispatch", "inspector", "--review", work.name, "--partition", "P1", capsys=capsys)
    assert code == 1
    assert "does not need inspecting" in err


# --- consolidation -----------------------------------------------------------------------


def test_the_consolidator_must_place_every_record_once(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    code, _, err = _submit(repo, work, d, {"failure_modes": [mode("empty", "R1-1")]}, capsys)
    assert code == 1
    assert "R1-2" in err
    both = {
        "duplicates": [{"record_id": "R1-2", "primary_id": "R1-1"}],
        "failure_modes": [mode("empty", "R1-1", "R1-2")],
    }
    code, _, err = _submit(repo, work, d, both, capsys)
    assert code == 1
    assert "more than once" in err


def test_a_duplicate_of_itself_says_so(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    output = {
        "duplicates": [{"record_id": "R1-2", "primary_id": "R1-2"}],
        "failure_modes": [mode("empty", "R1-1")],
    }
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "R1-2 cannot be a duplicate of itself" in err
    assert "itself a duplicate" not in err


def test_a_duplicate_of_a_duplicate_is_refused(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2"), claim(site="a.txt:3")], capsys)
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    output = {
        "duplicates": [
            {"record_id": "R1-2", "primary_id": "R1-1"},
            {"record_id": "R1-3", "primary_id": "R1-2"},
        ],
        "failure_modes": [mode("empty", "R1-1")],
    }
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "itself a duplicate" in err


def test_a_failure_mode_with_an_existing_name_joins_it(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("Empty values", "R1-1")])
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    data = _input(d)
    assert data["failure_modes"] == [{"name": "Empty values", "description": "how Empty values fails"}]
    assert [p["record_id"] for p in data["primaries"]] == ["R1-1"]
    _submitted(repo, work, d, {"failure_modes": [mode("empty  values", "R1-2")]}, capsys)
    assert {r["grouping"]["failure_mode"] for r in _review(work)["records"]} == {"Empty values"}
    assert len(_review(work)["failure_modes"]) == 1


def test_the_consolidators_primaries_leave_out_duplicates(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    _consolidate(repo, work, capsys, duplicates=[{"record_id": "R1-2", "primary_id": "R1-1"}])
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    assert [p["record_id"] for p in _input(d)["primaries"]] == ["R1-1"]


# --- routing, runs, and verdicts ------------------------------------------------------------


def test_routing_sends_each_record_where_a_run_or_a_challenge_can_settle_it(repo, work, capsys):
    _inspect(
        repo,
        work,
        "P1",
        [claim(), claim(site="a.txt:2", input=None), claim(site="a.txt:3", source="none"), claim(site="a.txt:4")],
        capsys,
    )
    _consolidate(repo, work, capsys)
    pending = _pending(repo, work, capsys)
    assert pending["run"] == ["R1-1", "R1-3", "R1-4"]
    assert pending["challenge"] == ["R1-2"]
    _run_all(repo, work, capsys, {"R1-4": "not runnable"})
    assert _pending(repo, work, capsys)["challenge"] == ["R1-2", "R1-3", "R1-4"]


def test_a_not_runnable_verdict_needs_a_reason(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "runner", capsys=capsys)
    code, _, err = _submit(repo, work, d, {"results": [{"record_id": "R1-1", **run("not runnable")}]}, capsys)
    assert code == 1
    assert "reason" in err


def test_a_verdict_from_a_probe_that_missed_the_path_is_refused(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "runner", capsys=capsys)
    output = {"results": [{"record_id": "R1-1", **run("refuted", reached_path=False)}]}
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "reached the path" in err


def test_the_runner_must_return_every_assigned_id(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "runner", capsys=capsys)
    code, _, err = _submit(repo, work, d, {"results": [{"record_id": "R1-1", **run()}]}, capsys)
    assert code == 1
    assert "no result for: R1-2" in err


def test_a_record_list_separated_by_commas_names_the_spaced_form(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    _consolidate(repo, work, capsys)
    code, _, err = _cli(repo, "dispatch", "runner", "--review", work.name, "--records", "R1-1,R1-2", capsys=capsys)
    assert code == 1
    assert "--records R1-1 R1-2" in err


def test_a_runner_can_take_a_subset_of_the_waiting_records(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "runner", "--records", "R1-2", capsys=capsys)
    assert [r["record_id"] for r in _input(d)["records"]] == ["R1-2"]


def test_not_runnable_and_sourceless_confirmed_records_go_to_the_challenger(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2", source=None)], capsys)
    _consolidate(repo, work, capsys)
    _run_all(repo, work, capsys, {"R1-1": "not runnable"})
    assert _pending(repo, work, capsys)["challenge"] == ["R1-1", "R1-2"]


def test_runs_that_disagree_split_a_duplicate_back_out(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    _consolidate(repo, work, capsys, duplicates=[{"record_id": "R1-2", "primary_id": "R1-1"}])
    result = _run_all(repo, work, capsys, {"R1-2": "refuted"})
    assert result["split_record_ids"] == ["R1-2"]
    records = _records(work)
    assert records["R1-2"]["grouping"]["primary_id"] == "R1-1"
    assert records["R1-2"]["split"]["primary_id"] == "R1-1"
    assert records["R1-2"]["split"]["failure_mode"] == records["R1-1"]["grouping"]["failure_mode"]
    assert records["R1-2"]["split"]["dispatch_id"] == result["dispatch_id"]
    assert _verdict(work, records["R1-2"]) == "refuted"


def test_a_test_adversary_probe_that_could_not_run_goes_to_the_challenger(repo, work, capsys):
    d = _dispatch(repo, work, "test-adversary", capsys=capsys)
    probe = claim(run=run("not runnable", reached_path=False, reason="needs a live service"))
    _submitted(repo, work, d, {"read_through": 100, "test_paths": ["t.py"], "claims": [probe]}, capsys)
    _consolidate(repo, work, capsys)
    pending = _pending(repo, work, capsys)
    assert pending["run"] == []
    assert pending["challenge"] == ["R1-1"]


def test_a_lens_cannot_record_a_run(repo, work, capsys):
    d = _dispatch(repo, work, "quality-lens", capsys=capsys)
    code, _, err = _submit(repo, work, d, {"read_through": 100, "claims": [claim(run=run())]}, capsys)
    assert code == 1
    assert "only the test adversary, the forms checker, and the runner" in err


def test_the_challenger_gets_the_hunks_of_the_files_its_records_cite(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(input=None)], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "challenger", capsys=capsys)
    assert _input(d)["packet_ranges"] == [SECTIONS["Metadata"], FILES["a.txt"], SECTIONS["Source of truth"]]
    verdict = {"record_id": "R1-1", "verdict": "upheld", "strength": "strong", "argument": "the spec says so"}
    _submitted(repo, work, d, {"read_through": 100, "results": [verdict]}, capsys)
    assert _pending(repo, work, capsys)["hunt"] == {"mode R1-1": ["R1-1"]}


def test_a_challenger_can_revise_the_priority_with_a_reason(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(input=None, priority="low")], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "challenger", capsys=capsys)
    verdict = {
        "record_id": "R1-1",
        "verdict": "upheld",
        "strength": "strong",
        "argument": "the spec says so",
        "revised_priority": {"priority": "critical", "reason": "it loses data"},
    }
    _submitted(repo, work, d, {"read_through": 100, "results": [verdict], "review_critique": "too soft"}, capsys)
    stored = _records(work)["R1-1"]["challenge"]
    assert stored["revised_priority"] == {"priority": "critical", "reason": "it loses data"}
    assert stored["dispatch_id"] == d["dispatch_id"]


def test_a_hunter_can_drop_a_record_whose_source_does_not_support_it(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys)
    _run_all(repo, work, capsys)
    d = _dispatch(repo, work, "hunter", "--failure-mode", "mode R1-1", capsys=capsys)
    assert _input(d)["failure_mode"] == {"name": "mode R1-1", "description": "how mode R1-1 fails"}
    unsupported = [{"record_id": "R1-1", "expected_supported": False, "reason": "the spec allows empty values"}]
    filed = hunter_output(unsupported, claims=(claim(site="b.txt:1"),))
    code, _, err = _submit(repo, work, d, filed, capsys)
    assert code == 1
    assert "no checked record is supported" in err
    stopped = hunter_output(unsupported, expected="", searched=[], sites=[])
    result = _submitted(repo, work, d, stopped, capsys)
    assert result["record_ids"] == []
    pending = _pending(repo, work, capsys)
    assert pending["hunt"] == {}
    assert pending["consolidate"] == []
    record = _records(work)["R1-1"]
    assert record["hunt"]["dispatch_id"] == d["dispatch_id"]
    assert _verdict(work, record) == "unsupported"


def test_a_hunter_takes_a_failure_mode_by_name_in_any_case(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys)
    _run_all(repo, work, capsys)
    code, _, err = _cli(repo, "dispatch", "hunter", "--review", work.name, "--failure-mode", "other", capsys=capsys)
    assert code == 1
    assert "'mode R1-1'" in err
    d = _dispatch(repo, work, "hunter", "--failure-mode", "MODE  r1-1", capsys=capsys)
    assert _input(d)["failure_mode"]["name"] == "mode R1-1"


def hunter_output(expectations: list[dict], *sites: str, claims: tuple[dict, ...] = (), **kw) -> dict:
    """Return a hunter's output whose sites are the given ones and each claim's, every one with status `claims`."""
    places = [*sites, *(c["site"] for c in claims)]
    return {
        "read_through": 100,
        "expectations": expectations,
        "expected": "an empty value is refused wherever a value is read",
        "searched": ["every place that reads a value (the readers in a.txt and b.txt)"],
        "sites": [{"site": s, "status": "claims", "reason": "accepts the empty value"} for s in places],
        "claims": list(claims),
    } | kw


def _hunter(repo, work, capsys) -> dict:
    """Confirm one record at a.txt:1 in "empty values" and dispatch its hunter."""
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1")])
    _run_all(repo, work, capsys)
    return _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)


SUPPORTED = [{"record_id": "R1-1", "expected_supported": True, "reason": "spec"}]


@pytest.mark.parametrize("missing", ["expected", "searched", "sites"])
def test_a_hunter_that_searched_states_its_rule_its_search_and_its_sites(repo, work, capsys, missing):
    d = _hunter(repo, work, capsys)
    empty = {missing: "" if missing == "expected" else []}
    code, _, err = _submit(repo, work, d, hunter_output(SUPPORTED, "a.txt:1", **empty), capsys)
    assert code == 1
    assert f"{missing} is empty" in err
    _submitted(repo, work, d, hunter_output(SUPPORTED, "a.txt:1"), capsys)
    stored = _review_dispatch(work, d["dispatch_id"])
    assert stored["expected"] == "an empty value is refused wherever a value is read"
    assert stored["searched"] == ["every place that reads a value (the readers in a.txt and b.txt)"]
    assert stored["sites"] == [{"site": "a.txt:1", "status": "claims", "reason": "accepts the empty value"}]


def _site(site: str, status: str = "claims") -> dict:
    return {"site": site, "status": status, "reason": "line 4 decides it"}


@pytest.mark.parametrize("sites", [["a.txt:1"], ["a.txt:1", ("b.txt:1", "handled")]])
def test_a_hunters_claim_is_at_a_site_it_listed_as_claims(repo, work, capsys, sites):
    d = _hunter(repo, work, capsys)
    listed = [_site(s) if isinstance(s, str) else _site(*s) for s in sites]
    output = hunter_output(SUPPORTED, claims=(claim(site="b.txt:1"),), sites=listed)
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "claims.0 (site b.txt:1)" in err
    assert "status claims" in err
    _submitted(repo, work, d, hunter_output(SUPPORTED, "a.txt:1", claims=(claim(site="b.txt:1"),)), capsys)


def test_a_site_a_hunter_lists_as_claims_has_a_claim_or_a_given_record(repo, work, capsys):
    d = _hunter(repo, work, capsys)
    output = hunter_output(SUPPORTED, "a.txt:1", "b.txt:7")
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "sites.1 (site b.txt:7)" in err
    assert "add a claim" in err
    assert "a.txt:1" not in err


def test_a_hunters_sites_include_each_supported_record_it_was_given(repo, work, capsys):
    d = _hunter(repo, work, capsys)
    output = hunter_output(SUPPORTED, sites=[_site("a.txt:2", "handled")])
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "R1-1" in err
    assert '"a.txt:1"' in err
    assert "copy" in err


def test_a_hunter_that_found_no_record_supported_lists_no_site(repo, work, capsys):
    d = _hunter(repo, work, capsys)
    unsupported = [{"record_id": "R1-1", "expected_supported": False, "reason": "the spec allows it"}]
    _submitted(repo, work, d, {"read_through": 100, "expectations": unsupported}, capsys)
    assert _pending(repo, work, capsys)["hunt"] == {}


UNCHECKED = {"site": "b.txt:3", "status": "not checked", "reason": "the reader is generated at build time"}


def test_a_hunter_that_left_sites_unchecked_gets_one_follow_up_hunter(repo, work, capsys):
    _built(repo, work, capsys)
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [claim()], capsys)
    _inspect(repo, work, "P2", [], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1")])
    _run_all(repo, work, capsys)
    (first,) = _step(repo, work, capsys=capsys)["dispatches"]
    sites = [_site("a.txt:1"), _site("a.txt:5", "handled"), UNCHECKED]
    _record(repo, work, first, hunter_output(SUPPORTED, sites=sites), capsys)
    status = _status(repo, work, capsys)
    assert status["pending"]["hunt"] == {"empty values": []}
    assert status["next"].startswith("dispatch hunter")

    (second,) = _step(repo, work, capsys=capsys)["dispatches"]
    assert second["role"] == "hunter"
    assert _pending(repo, work, capsys)["hunt"] == {}
    given = _input(_review_dispatch(work, second["dispatch_id"]))
    assert given["failure_mode"]["name"] == "empty values"
    assert given["expected"] == "an empty value is refused wherever a value is read"
    assert given["searched"] == ["every place that reads a value (the readers in a.txt and b.txt)"]
    assert given["sites"] == [UNCHECKED]
    assert (given["records"], given["check_expectations"]) == ([], [])

    _record(repo, work, second, hunter_output([], sites=[UNCHECKED]), capsys)
    assert _pending(repo, work, capsys)["hunt"] == {}
    code, _, err = _cli(
        repo, "dispatch", "hunter", "--review", work.name, "--failure-mode", "empty values", capsys=capsys
    )
    assert code == 1
    assert "left to hunt" in err


def _second_round_record_in_a_hunted_mode(repo, work, capsys) -> dict:
    """Hunt "mode R1-1" in round 1, confirm R2-1 in it in round 2, and dispatch its round-two hunter."""
    _finish_round_one(repo, work, capsys)
    _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    _inspect(repo, work, "P1", [claim(site="a.txt:9", input_form="a value of only spaces")], capsys)
    _inspect(repo, work, "P2", [], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("mode R1-1", "R2-1")])
    _run_all(repo, work, capsys)
    return _dispatch(repo, work, "hunter", "--failure-mode", "mode R1-1", capsys=capsys)


def test_a_hunter_of_a_failure_mode_hunted_before_gets_the_earlier_hunt(repo, work, capsys):
    data = _input(_second_round_record_in_a_hunted_mode(repo, work, capsys))
    assert [r["record_id"] for r in data["records"]] == ["R2-1"]
    earlier = data["earlier_hunt"]
    assert earlier["expected"] == "an empty value is refused wherever a value is read"
    assert earlier["searched"] == ["every place that reads a value (the readers in a.txt and b.txt)"]
    assert earlier["sites"] == [{"site": "a.txt:1", "status": "claims", "reason": "accepts the empty value"}]
    assert "sites" not in data


def test_a_hunter_given_an_earlier_hunt_can_list_its_only_record_in_misgrouped(repo, work, capsys):
    hunter = _second_round_record_in_a_hunted_mode(repo, work, capsys)
    output = {
        "read_through": 100,
        "expectations": [{"record_id": "R2-1", "expected_supported": True, "reason": "spec"}],
        "misgrouped": [{"record_id": "R2-1", "reason": "it breaks the rule for values of only spaces"}],
        "expected": _input(hunter)["earlier_hunt"]["expected"],
        "searched": [],
        "sites": [],
        "claims": [],
    }
    _submitted(repo, work, hunter, output, capsys)
    assert _records(work)["R2-1"]["grouping"] is None
    assert _pending(repo, work, capsys)["consolidate"] == ["R2-1"]


def _follow_up_hunter(repo, work, capsys) -> dict:
    """Leave b.txt:3 not checked in "empty values" and dispatch the hunter that decides it."""
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [claim()], capsys)
    _inspect(repo, work, "P2", [], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1")])
    _run_all(repo, work, capsys)
    first = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    _submitted(repo, work, first, hunter_output(SUPPORTED, sites=[_site("a.txt:1"), UNCHECKED]), capsys)
    return _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)


@pytest.mark.parametrize(
    ("sites", "extra", "message"),
    [
        ([_site("a.txt:77", "handled")], {}, "b.txt:3"),
        ([_site("b.txt:3", "handled"), _site("c.txt:2", "handled")], {}, "c.txt:2"),
        ([_site("b.txt:3", "handled")], {"expected": "every value is accepted"}, "expected"),
        ([_site("b.txt:3", "handled")], {"searched": ["the generator"]}, "searched"),
    ],
    ids=["omits its site", "adds a site", "changes the rule", "changes the search"],
)
def test_a_follow_up_hunter_decides_exactly_the_sites_it_was_given(repo, work, capsys, sites, extra, message):
    second = _follow_up_hunter(repo, work, capsys)
    code, _, err = _submit(repo, work, second, hunter_output([], sites=sites, **extra), capsys)
    assert code == 1
    assert message in err


@pytest.mark.parametrize("status", ["handled", "not checked"])
def test_a_hunter_gives_each_supported_records_site_the_status_claims(repo, work, capsys, status):
    hunter = _hunter(repo, work, capsys)
    code, _, err = _submit(repo, work, hunter, hunter_output(SUPPORTED, sites=[_site("a.txt:1", status)]), capsys)
    assert code == 1
    assert "status claims" in err


def test_a_hunter_given_an_earlier_hunt_keeps_its_rule(repo, work, capsys):
    hunter = _second_round_record_in_a_hunted_mode(repo, work, capsys)
    supported = [{"record_id": "R2-1", "expected_supported": True, "reason": "spec"}]
    output = hunter_output(supported, "a.txt:9", expected="every value is accepted")
    code, _, err = _submit(repo, work, hunter, output, capsys)
    assert code == 1
    assert "earlier_hunt" in err


def test_a_hunter_gets_each_records_claim_without_its_run(repo, work, capsys):
    adversary = _dispatch(repo, work, "test-adversary", capsys=capsys)
    _submitted(repo, work, adversary, {"read_through": 100, "claims": [claim(site="b.txt:5", run=run())]}, capsys)
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1", "R1-2")])
    _run_all(repo, work, capsys)
    runner_view = _input(_review_dispatch(work, "D4"))["records"][0]
    assert set(runner_view) >= {"claim", "run", "verdict"}
    d = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    views = _input(d)["records"]
    assert [v["record_id"] for v in views] == ["R1-1", "R1-2"]
    for view in views:
        assert set(runner_view) - set(view) == {"run"}
        assert set(claim()) - set(view["claim"]) == set()
        assert "run" not in view["claim"]
        assert "uv run probe.py" not in json.dumps(view)
    assert views[1]["claim"]["site"] == "a.txt:1"


def test_the_consolidator_gets_what_each_failure_modes_hunter_searched(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:9")], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1"), mode("other values", "R1-2")])
    _run_all(repo, work, capsys, {"R1-2": "refuted"})
    hunter = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    sites = [_site("a.txt:1"), _site("b.txt:1"), _site("a.txt:5", "handled"), UNCHECKED]
    _submitted(repo, work, hunter, hunter_output(SUPPORTED, claims=(claim(site="b.txt:1"),), sites=sites), capsys)
    hunted, other = _input(_dispatch(repo, work, "consolidator", capsys=capsys))["failure_modes"]
    assert hunted == {
        "name": "empty values",
        "description": "how empty values fails",
        "expected": "an empty value is refused wherever a value is read",
        "searched": ["every place that reads a value (the readers in a.txt and b.txt)"],
        "sites": [
            {"site": "a.txt:1", "status": "claims"},
            {"site": "b.txt:1", "status": "claims"},
            {"site": "a.txt:5", "status": "handled"},
            {"site": "b.txt:3", "status": "not checked"},
        ],
    }
    assert other == {"name": "other values", "description": "how other values fails"}


def test_the_synthesizer_gets_each_hunts_search_and_the_latest_status_of_each_site(repo, work, capsys):
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [claim()], capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:9")], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1"), mode("other values", "R1-2")])
    _run_all(repo, work, capsys, {"R1-2": "refuted"})
    first = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    _submitted(repo, work, first, hunter_output(SUPPORTED, sites=[_site("a.txt:1"), UNCHECKED]), capsys)
    second = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    decided = {"site": "b.txt:3", "status": "handled", "reason": "line 8 of the generator refuses it"}
    _submitted(repo, work, second, hunter_output([], sites=[decided]), capsys)
    _check_all_forms_tested(repo, work, capsys)
    hunted, other = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))["failure_modes"]
    assert hunted["expected"] == "an empty value is refused wherever a value is read"
    assert hunted["searched"] == ["every place that reads a value (the readers in a.txt and b.txt)"]
    assert hunted["sites"] == [_site("a.txt:1"), decided]
    assert other == {"name": "other values", "description": "how other values fails"}


def _hunted_mode_with_a_later_record(repo, work, capsys) -> dict:
    """Hunt "empty values", then confirm an inspector's record in the same failure mode."""
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1")])
    _run_all(repo, work, capsys)
    hunter = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    _submitted(repo, work, hunter, hunter_output(SUPPORTED, "a.txt:1"), capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-2")])
    _run_all(repo, work, capsys)
    return hunter


def test_a_record_a_hunter_filed_starts_no_hunt(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1")])
    _run_all(repo, work, capsys)
    hunter = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    output = hunter_output(
        SUPPORTED,
        "a.txt:1",
        claims=(claim(site="b.txt:1", input_form="a value of spaces only"),),
        suspected_input_forms=["a value of spaces only"],
    )
    _submitted(repo, work, hunter, output, capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("values of spaces", "R1-2")])
    _run_all(repo, work, capsys)
    pending = _pending(repo, work, capsys)
    assert pending["hunt"] == {}
    assert pending["refine"] == [hunter["dispatch_id"]]


def test_a_failure_mode_is_hunted_once_in_a_round(repo, work, capsys):
    _hunted_mode_with_a_later_record(repo, work, capsys)
    assert _pending(repo, work, capsys)["hunt"] == {}
    code, _, err = _cli(
        repo, "dispatch", "hunter", "--review", work.name, "--failure-mode", "empty values", capsys=capsys
    )
    assert code == 1
    assert "no confirmed or upheld record left to hunt" in err


def test_a_later_record_in_a_hunted_failure_mode_goes_to_the_keeper(repo, work, capsys):
    _hunted_mode_with_a_later_record(repo, work, capsys)
    assert _pending(repo, work, capsys)["refine"] == ["R1-2"]
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    assert _input(keeper)["suspected_input_forms"] == [{"input_form": "empty value", "failure_mode": "empty values"}]
    assert _pending(repo, work, capsys)["refine"] == []


def test_a_record_in_a_failure_mode_no_hunter_searched_still_gets_a_hunter(repo, work, capsys):
    _hunted_mode_with_a_later_record(repo, work, capsys)
    _submitted(
        repo,
        work,
        _dispatch(repo, work, "quality-lens", capsys=capsys),
        {"read_through": 100, "claims": [claim(site="c.txt:1")]},
        capsys,
    )
    _consolidate(repo, work, capsys, failure_modes=[mode("other values", "R1-3")])
    _run_all(repo, work, capsys)
    pending = _pending(repo, work, capsys)
    assert pending["hunt"] == {"other values": ["R1-3"]}
    assert pending["refine"] == ["R1-2"]


BOTH = [*SUPPORTED, {"record_id": "R1-2", "expected_supported": True, "reason": "spec"}]
MISGROUPED = {"record_id": "R1-2", "reason": "it breaks the rule for values of spaces, not the one for empty values"}


def _hunter_of_two(repo, work, capsys) -> dict:
    """Confirm R1-1 (a.txt:1) and R1-2 (b.txt:1) in "empty values" and dispatch its hunter."""
    _inspect(repo, work, "P1", [claim()], capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1", "R1-2")])
    _run_all(repo, work, capsys)
    return _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)


def _move(repo, work, capsys) -> dict:
    """Have the hunter of "empty values" list R1-2 in misgrouped; return the hunter's dispatch."""
    d = _hunter_of_two(repo, work, capsys)
    sites = [_site("a.txt:1"), _site("b.txt:1", "handled")]
    _submitted(repo, work, d, hunter_output(BOTH, sites=sites, misgrouped=[MISGROUPED]), capsys)
    return d


def test_a_record_a_hunter_lists_in_misgrouped_is_ungrouped_again(repo, work, capsys):
    d = _move(repo, work, capsys)
    record = _records(work)["R1-2"]
    assert record["grouping"] is None
    assert record["run"]["verdict"] == "confirmed"
    assert record["misgrouped"] == [
        {"failure_mode": "empty values", "reason": MISGROUPED["reason"], "dispatch_id": d["dispatch_id"]}
    ]
    assert _records(work)["R1-1"]["grouping"]["failure_mode"] == "empty values"
    assert _pending(repo, work, capsys)["consolidate"] == ["R1-2"]


def test_a_record_made_a_duplicate_passes_its_own_duplicates_to_its_primary(repo, work, capsys):
    claims = [claim(), claim(site="a.txt:2"), claim(site="a.txt:3"), claim(site="a.txt:4")]
    _inspect(repo, work, "P1", claims, capsys)
    _consolidate(
        repo,
        work,
        capsys,
        duplicates=[{"record_id": "R1-2", "primary_id": "R1-1"}],
        failure_modes=[mode("m1", "R1-1", "R1-3"), mode("m2", "R1-4")],
    )
    _run_all(repo, work, capsys)
    hunter = _dispatch(repo, work, "hunter", "--failure-mode", "m1", capsys=capsys)
    both = [{"record_id": i, "expected_supported": True, "reason": "spec"} for i in ("R1-1", "R1-3")]
    moved = {"misgrouped": [{"record_id": "R1-1", "reason": "it breaks another rule"}]}
    _submitted(repo, work, hunter, hunter_output(both, "a.txt:3", **moved), capsys)
    _consolidate(repo, work, capsys, duplicates=[{"record_id": "R1-1", "primary_id": "R1-4"}], failure_modes=[])
    assert _records(work)["R1-2"]["grouping"]["primary_id"] == "R1-4"


def test_a_moved_record_is_not_judged_again_and_keeps_its_duplicates(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:7")], capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    duplicate = {"record_id": "R1-1", "primary_id": "R1-3"}
    _consolidate(repo, work, capsys, duplicates=[duplicate], failure_modes=[mode("empty values", "R1-2", "R1-3")])
    _run_all(repo, work, capsys)
    d = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    both = [{"record_id": i, "expected_supported": True, "reason": "spec"} for i in ("R1-2", "R1-3")]
    moved = {"record_id": "R1-3", "reason": "it breaks another rule"}
    sites = [_site("a.txt:7"), _site("b.txt:1", "handled")]
    _submitted(repo, work, d, hunter_output(both, sites=sites, misgrouped=[moved]), capsys)
    run_before = _records(work)["R1-3"]["run"]
    pending = _pending(repo, work, capsys)
    assert (pending["consolidate"], pending["run"], pending["challenge"]) == (["R1-3"], [], [])
    _consolidate(repo, work, capsys, failure_modes=[mode("values of spaces", "R1-3")])
    pending = _pending(repo, work, capsys)
    assert (pending["consolidate"], pending["run"], pending["challenge"]) == ([], [], [])
    records = _records(work)
    assert records["R1-3"]["run"] == run_before
    assert records["R1-1"]["grouping"]["primary_id"] == "R1-3"
    assert _verdict(work, records["R1-1"]) == "duplicate"


def test_a_record_split_from_its_primary_leaves_the_primarys_failure_mode_when_misgrouped(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:7")], capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    duplicate = {"record_id": "R1-3", "primary_id": "R1-1"}
    _consolidate(repo, work, capsys, duplicates=[duplicate], failure_modes=[mode("empty values", "R1-1", "R1-2")])
    assert _run_all(repo, work, capsys, {"R1-1": "refuted"})["split_record_ids"] == ["R1-3"]
    d = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    both = [{"record_id": i, "expected_supported": True, "reason": "spec"} for i in ("R1-2", "R1-3")]
    moved = {"record_id": "R1-3", "reason": "it breaks another rule"}
    _submitted(repo, work, d, hunter_output(both, "a.txt:7", misgrouped=[moved]), capsys)
    (view,) = _input(_dispatch(repo, work, "consolidator", capsys=capsys))["records"]
    assert (view["record_id"], view["failure_mode"], view["primary_id"]) == ("R1-3", None, None)
    _consolidate(repo, work, capsys, failure_modes=[mode("values of spaces", "R1-3")])
    assert rs.failure_mode_of(rs.Record.model_validate(_records(work)["R1-3"])) == "values of spaces"


def test_a_misgrouped_records_site_need_not_be_in_sites(repo, work, capsys):
    d = _hunter_of_two(repo, work, capsys)
    _submitted(repo, work, d, hunter_output(BOTH, "a.txt:1", misgrouped=[MISGROUPED]), capsys)
    assert [s["site"] for s in _review_dispatch(work, d["dispatch_id"])["sites"]] == ["a.txt:1"]


def test_a_site_listed_as_claims_is_not_matched_by_a_misgrouped_record(repo, work, capsys):
    d = _hunter_of_two(repo, work, capsys)
    output = hunter_output(BOTH, "a.txt:1", "b.txt:1", misgrouped=[MISGROUPED])
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "sites.1 (site b.txt:1)" in err


def test_a_hunter_that_lists_every_supported_record_in_misgrouped_is_refused(repo, work, capsys):
    d = _hunter(repo, work, capsys)
    output = hunter_output(SUPPORTED, "a.txt:1", misgrouped=[MISGROUPED | {"record_id": "R1-1"}])
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "write expected for the largest group of records that break one rule" in err
    assert _records(work)["R1-1"]["grouping"]["failure_mode"] == "empty values"


@pytest.mark.parametrize(
    ("expectations", "misgrouped", "message"),
    [
        (BOTH, [MISGROUPED | {"record_id": "R1-9"}], "R1-9, which is not one of your records"),
        (
            [SUPPORTED[0], {"record_id": "R1-2", "expected_supported": False, "reason": "the spec allows it"}],
            [MISGROUPED],
            "R1-2, which your expectations mark unsupported",
        ),
        (BOTH, [MISGROUPED, MISGROUPED], "R1-2 more than once"),
    ],
)
def test_misgrouped_lists_supported_given_records_once_each(repo, work, capsys, expectations, misgrouped, message):
    d = _hunter_of_two(repo, work, capsys)
    code, _, err = _submit(repo, work, d, hunter_output(expectations, "a.txt:1", misgrouped=misgrouped), capsys)
    assert code == 1
    assert message in err
    assert _records(work)["R1-2"]["grouping"]["failure_mode"] == "empty values"


def test_a_follow_up_hunter_leaves_misgrouped_empty(repo, work, capsys):
    first = _hunter(repo, work, capsys)
    _submitted(repo, work, first, hunter_output(SUPPORTED, sites=[_site("a.txt:1"), UNCHECKED]), capsys)
    second = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    output = hunter_output([], sites=[UNCHECKED], misgrouped=[MISGROUPED | {"record_id": "R1-1"}])
    code, _, err = _submit(repo, work, second, output, capsys)
    assert code == 1
    assert "misgrouped must be empty" in err
    _submitted(repo, work, second, hunter_output([], sites=[UNCHECKED]), capsys)
    assert _records(work)["R1-1"]["grouping"]["failure_mode"] == "empty values"


def test_the_consolidator_places_a_moved_record_outside_the_failure_mode_it_left(repo, work, capsys):
    hunter = _move(repo, work, capsys)
    entry = {"failure_mode": "empty values", "reason": MISGROUPED["reason"], "dispatch_id": hunter["dispatch_id"]}
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    (view,) = _input(d)["records"]
    assert (view["record_id"], view["failure_mode"], view["misgrouped"]) == ("R1-2", None, [entry])
    code, _, err = _submit(repo, work, d, {"failure_modes": [mode("Empty  values", "R1-2")]}, capsys)
    assert code == 1
    assert "R1-2 left failure mode 'empty values'" in err
    _submitted(repo, work, d, {"failure_modes": [mode("values of spaces", "R1-2")]}, capsys)
    assert _pending(repo, work, capsys)["hunt"] == {"values of spaces": ["R1-2"]}
    second = _dispatch(repo, work, "hunter", "--failure-mode", "values of spaces", capsys=capsys)
    (given,) = _input(second)["records"]
    assert (given["record_id"], given["misgrouped"]) == ("R1-2", [entry])


def test_a_moved_record_is_not_a_duplicate_of_a_record_in_the_failure_mode_it_left(repo, work, capsys):
    _move(repo, work, capsys)
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    output = {"duplicates": [{"record_id": "R1-2", "primary_id": "R1-1"}]}
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "R1-2 left failure mode 'empty values'" in err


def _two_modes_and_a_move(repo, work, capsys, *, hunt_other_first: bool) -> None:
    """Confirm R1-1 and R1-2 in "empty values" and R1-3 in "other values"; move R1-2 out of "empty values".

    With `hunt_other_first`, the hunter of "other values" finishes before the move.
    """
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:7")], capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    modes = [mode("empty values", "R1-1", "R1-2"), mode("other values", "R1-3")]
    _consolidate(repo, work, capsys, failure_modes=modes)
    _run_all(repo, work, capsys)
    if hunt_other_first:
        other = _dispatch(repo, work, "hunter", "--failure-mode", "other values", capsys=capsys)
        supported = [{"record_id": "R1-3", "expected_supported": True, "reason": "spec"}]
        _submitted(repo, work, other, hunter_output(supported, "b.txt:1"), capsys)
    d = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    _submitted(repo, work, d, hunter_output(BOTH, "a.txt:1", misgrouped=[MISGROUPED]), capsys)


def test_a_moved_record_placed_in_a_failure_mode_hunted_this_round_goes_to_the_keeper(repo, work, capsys):
    _two_modes_and_a_move(repo, work, capsys, hunt_other_first=True)
    _consolidate(repo, work, capsys, failure_modes=[mode("other values", "R1-2")])
    pending = _pending(repo, work, capsys)
    assert pending["hunt"] == {}
    assert pending["refine"] == ["R1-2"]


def test_a_moved_record_placed_in_a_failure_mode_not_hunted_yet_is_in_its_hunt(repo, work, capsys):
    _two_modes_and_a_move(repo, work, capsys, hunt_other_first=False)
    assert _pending(repo, work, capsys)["hunt"] == {"other values": ["R1-3"]}
    _consolidate(repo, work, capsys, failure_modes=[mode("other values", "R1-2")])
    pending = _pending(repo, work, capsys)
    assert pending["hunt"] == {"other values": ["R1-2", "R1-3"]}
    assert pending["refine"] == []
    d = _dispatch(repo, work, "hunter", "--failure-mode", "other values", capsys=capsys)
    assert [v["record_id"] for v in _input(d)["records"]] == ["R1-2", "R1-3"]


def test_a_record_listed_in_misgrouped_a_second_time_stays_and_the_synthesizer_is_told(repo, work, capsys):
    _round_one_lenses(repo, work, capsys)
    _two_modes_and_a_move(repo, work, capsys, hunt_other_first=False)
    first = _review(work)["dispatches"][-1]
    _consolidate(repo, work, capsys, failure_modes=[mode("other values", "R1-2")])
    second = _dispatch(repo, work, "hunter", "--failure-mode", "other values", capsys=capsys)
    supported = [{"record_id": i, "expected_supported": True, "reason": "spec"} for i in ("R1-2", "R1-3")]
    again = {"record_id": "R1-2", "reason": "it breaks a third rule"}
    _submitted(repo, work, second, hunter_output(supported, "b.txt:1", misgrouped=[again]), capsys)
    entries = [
        {"failure_mode": "empty values", "reason": MISGROUPED["reason"], "dispatch_id": first["dispatch_id"]},
        {"failure_mode": "other values", "reason": again["reason"], "dispatch_id": second["dispatch_id"]},
    ]
    record = _records(work)["R1-2"]
    assert record["grouping"]["failure_mode"] == "other values"
    assert record["misgrouped"] == entries
    pending = _pending(repo, work, capsys)
    assert (pending["consolidate"], pending["hunt"], pending["refine"]) == ([], {}, [])
    _check_all_forms_tested(repo, work, capsys)
    findings = {v["record_id"]: v for v in _input(_dispatch(repo, work, "synthesizer", capsys=capsys))["findings"]}
    assert findings["R1-2"]["misgrouped"] == entries
    assert findings["R1-1"]["misgrouped"] == []


def test_the_consolidator_restates_only_the_failure_mode_a_moved_record_left(repo, work, capsys):
    _two_modes_and_a_move(repo, work, capsys, hunt_other_first=False)
    restated = {"name": "Empty values", "description": "an empty value is read with no check", "record_ids": []}
    other = {"name": "other values", "description": "another description", "record_ids": ["R1-2"]}
    _consolidate(repo, work, capsys, failure_modes=[restated, other])
    assert _review(work)["failure_modes"] == [
        {"name": "empty values", "description": "an empty value is read with no check"},
        {"name": "other values", "description": "how other values fails"},
    ]
    assert _records(work)["R1-1"]["grouping"]["failure_mode"] == "empty values"


def test_synthesis_waits_while_a_moved_record_waits_for_consolidation(repo, work, capsys):
    _round_one_lenses(repo, work, capsys)
    _move(repo, work, capsys)
    code, _, err = _cli(repo, "dispatch", "synthesizer", "--review", work.name, capsys=capsys)
    assert code == 1
    assert '"consolidate": ["R1-2"]' in err


def test_submit_prints_the_reply_and_why(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    output = inspector_output(_input(d)["pending_input_forms"], [])
    first = _submitted(repo, work, d, output, capsys)
    again = _submitted(repo, work, d, output, capsys)
    for data in (first, again):
        assert list(data)[-1] == "reply"
        assert f"`recorded {d['dispatch_id']}`" in data["reply"]
        assert "bias" in data["reply"]


# --- keeper ------------------------------------------------------------------------------------


def test_the_keeper_gets_the_proposals_and_reports_and_saves_its_list(repo, work, capsys):
    builder = _dispatch(repo, work, "list-builder", "--component", "c", "--paths", "a.txt", capsys=capsys)
    proposal = {"feature": "values of c", "origin": "spec: c", "input_forms": ["empty value"], "paths": ["c.txt"]}
    _submitted(repo, work, builder, {"read_through": 100, "proposals": [proposal]}, capsys)
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    data = _input(keeper)
    assert data["proposals"] == [proposal]
    assert "packet" not in data
    assert {p["partition_id"] for p in data["pending"]["inspect"]} == {"P1", "P2"}
    output = {"partitions": [{"partition_id": "new-1", **proposal}], "changes": ["new-1: added"]}
    result = _submitted(repo, work, keeper, output, capsys)
    assert result["added"] == ["P3"]
    assert _pending(repo, work, capsys)["refine"] == []
    stored = next(x for x in _review(work)["dispatches"] if x["dispatch_id"] == builder["dispatch_id"])
    assert stored["keeper_dispatch_id"] == keeper["dispatch_id"]


def test_the_keeper_gets_too_coarse_partitions_only_in_too_coarse(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    _submitted(repo, work, d, too_coarse_output(), capsys)
    data = _input(_dispatch(repo, work, "keeper", capsys=capsys))
    assert data["too_coarse"] == [{"partition_id": "P1", "proposed_split": "by value kind"}]
    assert [p["partition_id"] for p in data["pending"]["inspect"]] == ["P2"]


# --- convergence and rounds --------------------------------------------------------------------


def _finish_round_one(repo, work, capsys) -> None:
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys)
    _run_all(repo, work, capsys)
    hunter = _dispatch(repo, work, "hunter", "--failure-mode", "mode R1-1", capsys=capsys)
    output = hunter_output(SUPPORTED, "a.txt:1", suspected_input_forms=["a value of only spaces"])
    _submitted(repo, work, hunter, output, capsys)
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    assert _input(keeper)["suspected_input_forms"] == [
        {"input_form": "a value of only spaces", "failure_mode": "mode R1-1"}
    ]
    forms = [*FORMS, "a value of only spaces"]
    part = {"partition_id": "P1", "feature": "values of a", "origin": "spec", "input_forms": forms, "paths": ["a.txt"]}
    _submitted(repo, work, keeper, {"partitions": [part], "changes": ["P1: new form"]}, capsys)


def test_start_round_waits_for_open_dispatches_and_verdicts(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    code, _, err = _cli(repo, "start-round", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "consolidate" in err


def test_round_two_converges_when_half_its_inspector_claims_repeat_earlier_ones(repo, work, capsys):
    _finish_round_one(repo, work, capsys)
    assert _ok(repo, "start-round", "--review", work.name, capsys=capsys)["round"] == 2
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    assert _input(d)["pending_input_forms"] == ["a value of only spaces"]
    claims = [claim(input_form="a value of only spaces"), claim(site="a.txt:9", input_form="a value of only spaces")]
    _submitted(repo, work, d, inspector_output(_input(d)["pending_input_forms"], claims), capsys)
    _consolidate(
        repo,
        work,
        capsys,
        duplicates=[{"record_id": "R2-1", "primary_id": "R1-1"}],
        failure_modes=[mode("mode R1-1", "R2-2")],
    )
    conv = _status(repo, work, capsys)["convergence"]
    assert conv["inspector_claims"] == 2
    assert conv["repeats"] == 1
    assert conv["grouped"] == 2
    assert conv["converged"] is True


def test_duplicates_within_one_batch_are_not_repeats(repo, work, capsys):
    _finish_round_one(repo, work, capsys)
    _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    forms = _input(d)["pending_input_forms"]
    claims = [claim(input_form=forms[0]), claim(input_form=forms[0], site="a.txt:5")]
    _submitted(repo, work, d, inspector_output(forms, claims), capsys)
    _consolidate(
        repo,
        work,
        capsys,
        duplicates=[{"record_id": "R2-2", "primary_id": "R2-1"}],
        failure_modes=[mode("spaces", "R2-1")],
    )
    assert _status(repo, work, capsys)["convergence"]["converged"] is False


# --- forms checker, checker, and synthesis --------------------------------------------------------


def _partition_loop_stopped(repo, work, capsys) -> None:
    """Run the keeper and the round-one roles and inspect both partitions with no claims, so the forms checker is next."""
    _all_round_one_roles(repo, work, capsys)
    for partition_id in ("P1", "P2"):
        _inspect(repo, work, partition_id, [], capsys)


def test_a_form_no_test_exercises_needs_a_probe(repo, work, capsys):
    _partition_loop_stopped(repo, work, capsys)
    d = _dispatch(repo, work, "forms-checker", capsys=capsys)
    pairs = [{"partition_id": p, "input_form": f} for p in ("P1", "P2") for f in FORMS]
    assert _input(d)["pending_input_forms"] == pairs
    coverage = [pair | {"tests": ["t.py::test"]} for pair in pairs]
    coverage[0]["tests"] = []
    output = {"read_through": 100, "test_paths": ["t.py"], "input_forms": coverage}
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "P1: empty value" in err
    coverage[0]["claims"] = [claim(run=run("test gap"))]
    data = _submitted(repo, work, d, output, capsys)
    assert data["record_ids"] == ["R1-1"]
    assert _pending(repo, work, capsys)["check_forms"] == []
    checked = _review(work)["checked_input_forms"]
    assert checked[0] == {"partition_id": "P1", "input_form": FORMS[0], "tests": [], "dispatch_id": d["dispatch_id"]}


def test_a_forms_checker_gets_the_feature_and_paths_of_each_partition_it_checks(repo, work, capsys):
    _partition_loop_stopped(repo, work, capsys)
    d = _dispatch(repo, work, "forms-checker", capsys=capsys)
    assert _input(d)["partitions"] == [
        {"partition_id": "P1", "feature": "values of a", "paths": ["a.txt"]},
        {"partition_id": "P2", "feature": "values of b", "paths": ["b.txt"]},
    ]


def test_each_partitions_untested_form_needs_its_own_probe(repo, work, capsys):
    _partition_loop_stopped(repo, work, capsys)
    d = _dispatch(repo, work, "forms-checker", capsys=capsys)
    coverage = [pair | {"tests": ["t.py::test"]} for pair in _input(d)["pending_input_forms"]]
    for entry in coverage:
        if entry["input_form"] == FORMS[0]:
            entry["tests"] = []
    coverage[0]["claims"] = [claim(run=run("test gap"))]
    code, _, err = _submit(repo, work, d, {"read_through": 100, "input_forms": coverage}, capsys)
    assert code == 1
    assert "P2: empty value" in err
    assert "P1: empty value" not in err


def test_a_forms_checker_claim_tests_the_form_it_sits_under(repo, work, capsys):
    _partition_loop_stopped(repo, work, capsys)
    d = _dispatch(repo, work, "forms-checker", capsys=capsys)
    coverage = [pair | {"tests": ["t.py::test"]} for pair in _input(d)["pending_input_forms"]]
    coverage[0]["claims"] = [claim(input_form=FORMS[1], run=run("test gap"))]
    code, _, err = _submit(repo, work, d, {"read_through": 100, "input_forms": coverage}, capsys)
    assert code == 1
    assert FORMS[1] in err


def test_the_checks_that_passed_before_the_review_are_recorded(repo, work):
    assert _review(work)["checks"] == [
        {"command": "uv run pytest", "passed": True, "ran": True},
        {"command": "prek run --all-files", "passed": True, "ran": True},
    ]
    assert "checker" not in rs.ROLES


def test_reviewing_despite_a_failing_check_needs_the_users_reason(repo, work, tmp_path, capsys):
    path = str(_packet_json(repo, tmp_path, base="failing checks"))
    argv = ["start-review", "--scope", "staged", "--packet-json", path, "--failed-checks", "uv run pytest", *VALUES]
    code, _, err = _cli(repo, *argv, capsys=capsys)
    assert code == 1
    assert "--reason" in err
    reason = "the failing test fails the same way on main"
    work = _start(
        repo, tmp_path, capsys, "--failed-checks", "uv run pytest", "--reason", reason, base="failing checks"
    )
    _judged_review(repo, work, capsys, introduced="pre-existing")
    data = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))
    assert data["merge_readiness"] == "unverified"
    assert data["checks"] == [{"command": "uv run pytest", "passed": False, "ran": True}]
    assert data["checks_reason"] == reason


def test_a_check_that_did_not_run_needs_the_users_reason_and_leaves_merge_readiness_unverified(
    repo, work, tmp_path, capsys
):
    path = str(_packet_json(repo, tmp_path, base="skipped checks"))
    checks = ["--passed-checks", "uv run pytest", "--skipped-checks", "just test integration"]
    code, _, err = _cli(
        repo, "start-review", "--scope", "staged", "--packet-json", path, *checks, *VALUES, capsys=capsys
    )
    assert code == 1
    assert "--reason" in err
    reason = "the integration tests need database containers"
    work = _start(repo, tmp_path, capsys, *checks, "--reason", reason, base="skipped checks")
    _judged_review(repo, work, capsys, introduced="pre-existing")
    data = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))
    assert data["merge_readiness"] == "unverified"
    assert data["checks"] == [
        {"command": "uv run pytest", "passed": True, "ran": True},
        {"command": "just test integration", "passed": False, "ran": False},
    ]
    assert data["checks_reason"] == reason


def test_two_reviews_finished_in_one_second_write_two_reports(repo, work, tmp_path, capsys, monkeypatch):
    class Frozen(rs._dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return rs._dt.datetime(2026, 11, 13, 16, 40, 0, tzinfo=tz)

    works = []
    for base in ("first", "second"):
        path = str(_packet_json(repo, tmp_path, base=base))
        argv = ("start-review", "--scope", "staged", "--packet-json", path, *TEXT_VALUES)
        works.append(Path(_ok(repo, *argv, capsys=capsys)["path"]))
    monkeypatch.setattr(rs._dt, "datetime", Frozen)
    paths = []
    for review in works:
        _round_one_lenses(repo, review, capsys)
        paths.append(_input(_dispatch(repo, review, "synthesizer", capsys=capsys))["output_path"])
    assert paths[0] != paths[1]


def _judged_review(repo, work, capsys, p2_claims=(), challenger_output=None, **kw) -> None:
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [claim(**kw)], capsys)
    _inspect(repo, work, "P2", list(p2_claims), capsys)
    _consolidate(repo, work, capsys)
    _run_all(repo, work, capsys)
    hunter = _dispatch(repo, work, "hunter", "--failure-mode", "mode R1-1", capsys=capsys)
    _submitted(repo, work, hunter, hunter_output(SUPPORTED, claim(**kw)["site"]), capsys)
    if challenger_output is not None:
        _submitted(repo, work, _dispatch(repo, work, "challenger", capsys=capsys), challenger_output, capsys)
    _check_all_forms_tested(repo, work, capsys)


# --- standard review -------------------------------------------------------------------------


@pytest.fixture
def standard_work(repo, tmp_path, capsys) -> Path:
    """Save a partition for each changed file and start a review that names no depth."""
    _save(
        repo,
        [
            {"partition_id": f"new-{n}", "feature": f"values of {name}", "origin": "spec", "input_forms": FORMS}
            | {"paths": [f"{name}.txt"]}
            for n, name in enumerate(("a", "b"), start=1)
        ],
    )
    path = str(_packet_json(repo, tmp_path))
    data = _ok(repo, "start-review", "--scope", "staged", "--packet-json", path, *TEXT_VALUES, capsys=capsys)
    return Path(data["path"])


def test_status_lists_the_unfinished_reviews(repo, standard_work, capsys):
    _dispatch(repo, standard_work, "security-lens", capsys=capsys)
    unfinished = _ok(repo, "status", "--scope", "staged", capsys=capsys)["unfinished_reviews"]
    assert [u["review_id"] for u in unfinished] == [standard_work.name]
    assert unfinished[0]["depth"] == "standard"
    assert unfinished[0]["open_dispatches"] == 1


def test_a_review_keeps_the_users_model_choices(repo, standard_work, capsys):
    _update(repo, standard_work, "--models", "strong: opus; small: haiku", capsys=capsys)
    assert _status(repo, standard_work, capsys)["models"] == "strong: opus; small: haiku"


def test_a_standard_review_gives_each_challenger_at_most_twelve_records(repo, standard_work, capsys):
    claims = [claim(site=f"a.txt:{n}") for n in range(1, 14)]
    _standard_lens_claims(repo, standard_work, capsys, *claims)
    _consolidate(repo, standard_work, capsys)
    sizes = [
        len(_input(_review_dispatch(standard_work, d["dispatch_id"]))["records"])
        for d in _step(repo, standard_work, capsys=capsys)["dispatches"]
    ]
    assert sizes == [12, 1]


def test_a_component_given_again_to_an_open_dispatch_with_other_paths_is_refused(repo, standard_work, capsys):
    _component(repo, standard_work, "quality-lens", "a", "a.txt", capsys=capsys)
    code, _, err = _component(repo, standard_work, "quality-lens", "a", "b.txt", capsys=capsys)
    assert code == 1
    assert "a.txt" in err


def test_a_deep_review_takes_its_components_from_the_list_builders(repo, standard_work, capsys):
    _component(repo, standard_work, "quality-lens", "core", "a.txt", capsys=capsys)
    _update(repo, standard_work, "--depth", "deep", capsys=capsys)
    _dispatch(repo, standard_work, "list-builder", "--component", "core", "--paths", "a.txt", "b.txt", capsys=capsys)
    assert rs._component_paths(rs.read_review(standard_work)) == {"core": ["a.txt", "b.txt"]}


def test_a_challenged_record_that_becomes_a_duplicate_in_a_deep_review_is_not_left_waiting(
    repo, standard_work, capsys
):
    _standard_lens_claims(repo, standard_work, capsys, claim(), claim(site="a.txt:2"))
    _consolidate(repo, standard_work, capsys)
    _challenge(repo, standard_work, capsys, {"R1-1": ("upheld", "strong"), "R1-2": ("upheld", "strong")})
    _update(repo, standard_work, "--depth", "deep", capsys=capsys)
    record = _records(standard_work)["R1-2"] | {"grouping": {"primary_id": "R1-1", "dispatch_id": "D9"}}
    assert _verdict(standard_work, record) == "duplicate"


def test_a_review_started_with_no_depth_is_a_standard_review(repo, standard_work, capsys):
    assert _review(standard_work)["depth"] == "standard"
    assert _status(repo, standard_work, capsys)["depth"] == "standard"


def test_a_standard_review_goes_from_the_lenses_to_the_synthesizer_with_no_partition_role(repo, standard_work, capsys):
    first = _status(repo, standard_work, capsys)["next"]
    assert "quality-lens" in first
    assert "list-builder" not in first
    _round_one_lenses(repo, standard_work, capsys)
    status = _status(repo, standard_work, capsys)
    assert status["pending"]["inspect"] == []
    assert status["pending"]["check_forms"] == []
    assert status["next"] == "dispatch synthesizer"
    d = _dispatch(repo, standard_work, "synthesizer", capsys=capsys)
    assert _input(d)["depth"] == "standard"
    assert _input(d)["inspections"] == []


@pytest.mark.parametrize(
    "request_",
    [
        ("list-builder", "--component", "a", "--paths", "a.txt"),
        ("keeper",),
        ("inspector", "--partition", "P1"),
        ("forms-checker",),
        ("runner",),
        ("hunter", "--failure-mode", "empty values"),
    ],
    ids=lambda r: r[0],
)
def test_a_standard_review_dispatches_no_role_of_the_deep_review(repo, standard_work, capsys, request_):
    _round_one_lenses(repo, standard_work, capsys)
    code, _, err = _cli(repo, "dispatch", *request_, "--review", standard_work.name, capsys=capsys)
    assert code == 1
    assert f"a standard review does not dispatch a {request_[0]}" in err
    assert "--depth deep" in err


def test_a_standard_review_starts_no_round(repo, standard_work, capsys):
    _round_one_lenses(repo, standard_work, capsys)
    code, _, err = _cli(repo, "start-round", "--review", standard_work.name, capsys=capsys)
    assert code == 1
    assert "standard review" in err
    assert "converged" not in err


def _standard_lens_claims(repo, work, capsys, *claims: dict) -> None:
    lens = _dispatch(repo, work, "quality-lens", capsys=capsys)
    _submitted(repo, work, lens, {"read_through": 100, "claims": list(claims)}, capsys)
    _round_one_lenses(repo, work, capsys)


def test_a_standard_review_sends_a_lens_claim_to_the_challenger_and_then_reports(repo, standard_work, capsys):
    _standard_lens_claims(repo, standard_work, capsys, claim())
    _consolidate(repo, standard_work, capsys, failure_modes=[mode("empty values", "R1-1")])
    pending = _pending(repo, standard_work, capsys)
    assert pending["run"] == []
    assert pending["challenge"] == ["R1-1"]
    _challenge(repo, standard_work, capsys, {"R1-1": ("upheld", "strong")})
    status = _status(repo, standard_work, capsys)
    assert status["pending"]["hunt"] == {}
    assert status["next"] == "dispatch synthesizer"


def test_a_standard_review_drops_a_duplicate_claim_without_a_run(repo, standard_work, capsys):
    _standard_lens_claims(repo, standard_work, capsys, claim(), claim(site="a.txt:2"))
    duplicate = {"record_id": "R1-2", "primary_id": "R1-1"}
    _consolidate(repo, standard_work, capsys, [duplicate], [mode("empty values", "R1-1")])
    assert _records(standard_work)["R1-2"]["grouping"]["primary_id"] == "R1-1"
    status = _status(repo, standard_work, capsys)
    assert status["pending"]["challenge"] == ["R1-1"]
    assert status["candidates"] == ["R1-1"]


def test_a_standard_review_keeps_the_verdict_of_a_test_adversary_run(repo, standard_work, capsys):
    adversary = _dispatch(repo, standard_work, "test-adversary", capsys=capsys)
    output = {"read_through": 100, "test_paths": [], "already_tested": 0, "claims": [claim(run=run("test gap"))]}
    _submitted(repo, standard_work, adversary, output, capsys)
    _round_one_lenses(repo, standard_work, capsys)
    _consolidate(repo, standard_work, capsys, failure_modes=[mode("empty values", "R1-1")])
    assert _status(repo, standard_work, capsys)["next"] == "dispatch synthesizer"


def _component(repo, work, role: str, name: str, *paths: str, capsys) -> tuple[int, dict | None, str]:
    extra = ("--paths", *paths) if paths else ()
    return _cli(repo, "dispatch", role, "--review", work.name, "--component", name, *extra, capsys=capsys)


def test_a_standard_review_takes_a_component_from_the_quality_lens_or_the_test_adversary(repo, standard_work, capsys):
    lens = _dispatch(repo, standard_work, "quality-lens", "--component", "a", "--paths", "a.txt", capsys=capsys)
    data = _input(lens)
    assert (data["component"], data["paths"]) == ("a", ["a.txt"])
    assert FILES["a.txt"] in [list(r) for r in data["packet_ranges"]]
    assert FILES["b.txt"] not in [list(r) for r in data["packet_ranges"]]
    adversary = _dispatch(repo, standard_work, "test-adversary", "--component", "a", capsys=capsys)
    assert _input(adversary)["paths"] == ["a.txt"]
    other = _dispatch(repo, standard_work, "test-adversary", "--component", "b", "--paths", "b.txt", capsys=capsys)
    assert _input(other)["paths"] == ["b.txt"]


def test_each_component_of_a_standard_review_needs_its_quality_lens_and_its_test_adversary(
    repo, standard_work, capsys
):
    _component(repo, standard_work, "quality-lens", "a", "a.txt", capsys=capsys)
    _component(repo, standard_work, "test-adversary", "b", "b.txt", capsys=capsys)
    missing = rs._round_one_missing(rs.read_review(standard_work))
    assert "quality-lens --component b" in missing
    assert "test-adversary --component a" in missing
    assert "quality-lens" not in missing
    assert "test-adversary" not in missing


def test_a_standard_review_names_the_changed_files_that_are_in_no_component(repo, standard_work, capsys):
    lens = _dispatch(repo, standard_work, "quality-lens", "--component", "a", "--paths", "a.txt", capsys=capsys)
    _submitted(repo, standard_work, lens, {"read_through": 100}, capsys)
    missing = rs._round_one_missing(rs.read_review(standard_work))
    assert "quality-lens --component <name> --paths b.txt" in missing
    assert "b.txt" in _status(repo, standard_work, capsys)["next"]


def test_a_standard_review_takes_a_limited_number_of_components(repo, standard_work, capsys, monkeypatch):
    monkeypatch.setattr(rs, "COMPONENT_LIMIT", 1)
    _component(repo, standard_work, "quality-lens", "a", "a.txt", capsys=capsys)
    code, _, err = _component(repo, standard_work, "quality-lens", "b", "b.txt", capsys=capsys)
    assert code == 1
    assert "at most 1" in err


def test_a_changed_file_is_in_one_component_only(repo, standard_work, capsys):
    _component(repo, standard_work, "quality-lens", "a", "a.txt", capsys=capsys)
    code, _, err = _component(repo, standard_work, "test-adversary", "b", "a.txt", "b.txt", capsys=capsys)
    assert code == 1
    assert "a.txt is in component 'a'" in err


def test_a_component_given_again_with_other_paths_is_refused(repo, standard_work, capsys):
    _component(repo, standard_work, "quality-lens", "a", "a.txt", capsys=capsys)
    code, _, err = _component(repo, standard_work, "test-adversary", "a", "b.txt", capsys=capsys)
    assert code == 1
    assert "component 'a' has the paths a.txt" in err


def test_a_component_with_no_paths_must_be_a_known_one(repo, standard_work, capsys):
    code, _, err = _component(repo, standard_work, "test-adversary", "a", capsys=capsys)
    assert code == 1
    assert "--paths" in err


def test_each_component_of_a_deep_review_needs_its_test_adversary(repo, work, capsys):
    _builders(repo, work, capsys, "a", "b")
    missing = rs._round_one_missing(rs.read_review(work))
    assert "test-adversary --component a" in missing
    assert "test-adversary --component b" in missing
    assert "test-adversary" not in missing
    d = _dispatch(repo, work, "test-adversary", "--component", "b", capsys=capsys)
    assert _input(d)["paths"] == ["b.txt"]


def test_a_standard_review_changed_to_deep_builds_the_list_and_inspects_the_partitions(repo, standard_work, capsys):
    _round_one_lenses(repo, standard_work, capsys)
    _update(repo, standard_work, "--depth", "deep", capsys=capsys)
    assert _status(repo, standard_work, capsys)["next"] == "dispatch list-builder for each component"
    keeper = _dispatch(repo, standard_work, "keeper", capsys=capsys)
    _submitted(repo, standard_work, keeper, {"partitions": []}, capsys)
    status = _status(repo, standard_work, capsys)
    assert [p["partition_id"] for p in status["pending"]["inspect"]] == ["P1", "P2"]
    assert status["plan_frozen"] is False


def _check_all_forms_tested(repo, work, capsys) -> None:
    d = _dispatch(repo, work, "forms-checker", capsys=capsys)
    coverage = [pair | {"tests": ["t.py::test"]} for pair in _input(d)["pending_input_forms"]]
    _submitted(repo, work, d, {"read_through": 100, "input_forms": coverage}, capsys)


def test_synthesis_waits_until_every_record_has_a_verdict(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    code, _, err = _cli(repo, "dispatch", "synthesizer", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "R1-1" in err


def test_a_confirmed_defect_the_change_introduced_blocks_the_merge(repo, work, capsys):
    _judged_review(repo, work, capsys)
    data = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))
    assert data["merge_readiness"] == "no"
    assert data["findings"][0]["blocking"] is True
    assert data["findings"][0]["confidence"] == "high"


def test_a_pre_existing_defect_is_reported_but_does_not_block(repo, work, capsys):
    _judged_review(repo, work, capsys, introduced="pre-existing")
    data = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))
    assert data["findings"][0]["blocking"] is False
    assert data["merge_readiness"] == "yes"


def test_the_synthesizer_gets_the_lens_summaries_the_list_changes_and_the_critiques(repo, work, capsys):
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    _submitted(repo, work, keeper, {"partitions": [], "changes": ["P1: added a form"]}, capsys)
    lens = _dispatch(repo, work, "security-lens", capsys=capsys)
    _submitted(repo, work, lens, {"read_through": 100, "summary": "A01-A10 clean"}, capsys)
    verdict = {"record_id": "R1-2", "verdict": "refuted", "strength": "strong", "argument": "intended"}
    _judged_review(
        repo,
        work,
        capsys,
        p2_claims=[claim(site="b.txt:1", input=None, priority="low")],
        challenger_output={"read_through": 100, "results": [verdict], "review_critique": "too soft"},
    )
    data = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))
    assert data["lens_summaries"] == [{"role": "security-lens", "component": None, "summary": "A01-A10 clean"}]
    assert data["list_changes"] == ["P1: added a form"]
    assert data["review_critiques"] == ["too soft"]
    assert [m["name"] for m in data["failure_modes"]] == ["mode R1-1", "mode R1-2"]


def test_the_report_must_name_every_record(repo, work, capsys):
    _judged_review(repo, work, capsys)
    d = _dispatch(repo, work, "synthesizer", capsys=capsys)
    code, _, err = _submit(repo, work, d, "# Report\n\nNothing here.\n", capsys)
    assert code == 1
    assert "R1-1" in err
    _submitted(repo, work, d, "# Report\n\n- R1-1: an empty value is accepted\n", capsys)


def test_synthesis_waits_for_claims_that_carry_their_own_runs(repo, work, capsys):
    _judged_review(repo, work, capsys)
    adversary = _dispatch(repo, work, "test-adversary", capsys=capsys)
    output = {"read_through": 100, "claims": [claim(site="b.txt:1", run=run())]}
    _submitted(repo, work, adversary, output, capsys)
    code, _, err = _cli(repo, "dispatch", "synthesizer", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "consolidate" in err


def test_a_disputed_finding_waits_for_the_users_ruling(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(input=None)], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "challenger", capsys=capsys)
    verdict = {"record_id": "R1-1", "verdict": "disputed", "strength": "moderate", "argument": "both sides hold"}
    _submitted(repo, work, d, {"read_through": 100, "results": [verdict]}, capsys)
    pending = _pending(repo, work, capsys)
    assert pending["rule"] == ["R1-1"]
    assert pending["hunt"] == {}
    argv = ["rule", "R1-1", "--review", work.name, "--verdict", "upheld", "--reason", "the spec is clear"]
    first = _ok(repo, *argv, capsys=capsys)
    assert first == {"record_id": "R1-1", "verdict": "upheld", "already_ruled": False}
    pending = _pending(repo, work, capsys)
    assert pending["rule"] == []
    assert pending["hunt"] == {"mode R1-1": ["R1-1"]}
    assert _records(work)["R1-1"]["ruling"] == {"verdict": "upheld", "reason": "the spec is clear"}
    assert _ok(repo, *argv, capsys=capsys) == first | {"already_ruled": True}
    code, _, err = _cli(
        repo, "rule", "R1-1", "--review", work.name, "--verdict", "refuted", "--reason", "changed", capsys=capsys
    )
    assert code == 1
    assert "already ruled upheld" in err


def test_the_runner_cannot_record_a_test_gap(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "runner", capsys=capsys)
    code, _, err = _submit(repo, work, d, {"results": [{"record_id": "R1-1", **run("test gap")}]}, capsys)
    assert code == 1
    assert "verdict" in err


def test_a_partition_reported_too_coarse_waits_for_the_keeper(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    _submitted(repo, work, d, too_coarse_output(), capsys)
    pending = _pending(repo, work, capsys)
    assert "P1" not in [n["partition_id"] for n in pending["inspect"]]
    assert pending["refine"] == [d["dispatch_id"]]
    code, _, err = _cli(repo, "dispatch", "inspector", "--review", work.name, "--partition", "P1", capsys=capsys)
    assert code == 1
    assert "too coarse" in err
    assert "keeper" in err


@pytest.mark.parametrize("reason", ["", "   "])
def test_a_ruling_needs_a_reason(repo, work, capsys, reason):
    _inspect(repo, work, "P1", [claim(input=None)], capsys)
    _consolidate(repo, work, capsys)
    d = _dispatch(repo, work, "challenger", capsys=capsys)
    verdict = {"record_id": "R1-1", "verdict": "disputed", "strength": "moderate", "argument": "both sides hold"}
    _submitted(repo, work, d, {"read_through": 100, "results": [verdict]}, capsys)
    argv = ["rule", "R1-1", "--review", work.name, "--verdict", "refuted", "--reason", reason]
    code, _, err = _cli(repo, *argv, capsys=capsys)
    assert code == 1
    assert "--reason" in err
    assert _pending(repo, work, capsys)["rule"] == ["R1-1"]


def test_next_names_one_step_in_the_procedures_order(repo, work, capsys):
    assert _status(repo, work, capsys)["next"] == "dispatch list-builder for each component"
    builder = _dispatch(repo, work, "list-builder", "--component", "a", "--paths", "a.txt", capsys=capsys)
    _submitted(repo, work, builder, {"read_through": 100, "proposals": []}, capsys)
    assert _status(repo, work, capsys)["next"] == "dispatch keeper"
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    _submitted(repo, work, keeper, {"partitions": []}, capsys)
    first = _status(repo, work, capsys)["next"]
    assert first.startswith("dispatch inspector")
    assert first.endswith("spec-lens")
    _inspect(repo, work, "P1", [claim()], capsys)
    _inspect(repo, work, "P2", [], capsys)
    assert _status(repo, work, capsys)["next"] == "dispatch quality-lens, security-lens, test-adversary, spec-lens"


def _some_work(repo, work, capsys) -> None:
    lens = _dispatch(repo, work, "quality-lens", capsys=capsys)
    _submitted(repo, work, lens, {"read_through": 100}, capsys)


def test_a_third_round_does_not_start(repo, work, capsys):
    _round_one_lenses(repo, work, capsys)
    _some_work(repo, work, capsys)
    assert _ok(repo, "start-round", "--review", work.name, capsys=capsys)["round"] == 2
    _some_work(repo, work, capsys)
    code, _, err = _cli(repo, "start-round", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "round 2 is the last round" in err


def test_a_deep_review_freezes_the_plan_when_its_second_round_is_inspected(repo, work, capsys):
    _finish_round_one(repo, work, capsys)
    _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    assert _status(repo, work, capsys)["plan_frozen"] is False
    _inspect(repo, work, "P1", [], capsys)
    _inspect(repo, work, "P2", [], capsys)
    status = _status(repo, work, capsys)
    assert status["convergence"]["converged"] is False
    assert status["plan_frozen"] is True
    assert status["next"] == "dispatch forms-checker"


def test_starting_a_round_again_before_any_dispatch_returns_the_started_round(repo, work, capsys):
    _round_one_lenses(repo, work, capsys)
    first = _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    again = _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    assert first["round"] == again["round"] == 2
    assert (first["already_started"], again["already_started"]) == (False, True)
    assert again["finished_round"] == first["finished_round"]


def test_starting_a_review_again_from_the_same_packet_returns_the_started_review(repo, tmp_path, capsys):
    path = str(_packet_json(repo, tmp_path))
    first = _ok(repo, "start-review", "--scope", "staged", "--packet-json", path, *VALUES, capsys=capsys)
    again = _ok(repo, "start-review", "--scope", "staged", "--packet-json", path, *VALUES, capsys=capsys)
    assert first["already_started"] is False
    assert again == first | {"already_started": True}
    assert len(list((repo / ".review" / "reviews").iterdir())) == 1


def test_starting_a_review_again_with_other_values_is_refused(repo, tmp_path, capsys):
    start = ("start-review", "--scope", "staged", "--packet-json", str(_packet_json(repo, tmp_path)))
    first = _ok(repo, *start, *VALUES, capsys=capsys)
    other = ("--intent", "allow empty values", "--how-to-run", VALUES[3], "--architecture", "yes")
    code, _, err = _cli(repo, *start, *other, capsys=capsys)
    assert code == 1
    assert "--intent, --architecture" in err
    assert "--how-to-run" not in err
    assert f"update-review --review {first['review_id']}" in err
    stored = _review(Path(first["path"]))
    assert (stored["intent"], stored["architecture"]) == (VALUES[1], False)


def test_starting_a_review_again_compares_only_the_values_it_gives(repo, tmp_path, capsys):
    start = ("start-review", "--scope", "staged", "--packet-json", str(_packet_json(repo, tmp_path)))
    first = _ok(repo, *start, *VALUES, "--architecture", "yes", "--spec", "docs/prd.md", capsys=capsys)
    again = _ok(repo, *start, *VALUES, capsys=capsys)
    assert again == first | {"already_started": True}
    stored = _review(Path(first["path"]))
    assert (stored["architecture"], stored["spec"], stored["feature_type"]) == (True, "docs/prd.md", "other")


def test_a_list_builder_dispatched_again_with_other_paths_is_refused(repo, work, capsys):
    first = _dispatch(repo, work, "list-builder", "--component", "a", "--paths", "a.txt", capsys=capsys)
    same = _dispatch(repo, work, "list-builder", "--component", "a", "--paths", "a.txt", capsys=capsys)
    assert same["already_dispatched"] is True
    argv = ("dispatch", "list-builder", "--component", "a", "--paths", "a.txt", "b.txt", "--review", work.name)
    code, _, err = _cli(repo, *argv, capsys=capsys)
    assert code == 1
    assert first["dispatch_id"] in err
    assert "a.txt b.txt" in err
    assert _review_dispatch(work, first["dispatch_id"])["paths"] == ["a.txt"]


def test_review_commands_reach_the_review_from_another_directory_with_repo(repo, work, tmp_path, monkeypatch, capsys):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    _git(elsewhere, "init", "-q")
    monkeypatch.chdir(elsewhere)
    data = _ok(repo, "status", "--review", work.name, capsys=capsys)
    assert [n["partition_id"] for n in data["pending"]["inspect"]] == ["P1", "P2"]
    code = rs.main(["status", "--review", work.name])
    _, err = capsys.readouterr()
    assert code == 1
    assert "--repo" in err


def test_a_command_outside_any_repository_says_to_pass_repo(tmp_path, capsys):
    code, _, err = _cli(tmp_path, "status", "--scope", "staged", capsys=capsys)
    assert code == 1
    assert "pass --repo" in err


def test_every_input_file_names_the_repository_root(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    assert _input(d)["root"] == str(repo.resolve())
    assert _review(work)["root"] == str(repo.resolve())


def test_schema_takes_the_role(repo, capsys):
    data = _ok(repo, "schema", "hunter", capsys=capsys)
    assert data["title"] == "HunterOutput"
    for field in ("expected", "searched", "sites"):
        assert data["properties"][field]["description"], field
    assert data["$defs"]["HuntSite"]["properties"]["status"]["enum"] == ["handled", "claims", "not checked"]
    assert data["$defs"]["HuntSite"]["properties"]["reason"]["description"]
    assert _ok(repo, "schema", "synthesizer", capsys=capsys)["format"].startswith("markdown")


# --- templates ------------------------------------------------------------------------------------


def test_every_role_has_one_complete_registry_entry():
    assert set(rs.ROLE_SPECS) == set(rs.ROLES)
    for role, spec in rs.ROLE_SPECS.items():
        assert (spec.output is None) == (spec.apply is None), role
    assert {r for r, s in rs.ROLE_SPECS.items() if s.lens} == {"quality-lens", "security-lens", "spec-lens"}


def test_every_role_has_a_template_named_for_it():
    assets = SCRIPT.parents[1] / "assets"
    assert {p.stem.removeprefix("prompt-") for p in assets.glob("prompt-*.md")} == set(rs.ROLES)


def test_the_claim_template_lists_exactly_the_schema_fields():
    text = (SCRIPT.parents[1] / "assets" / "claim.md").read_text().split("\nPriority:")[0]
    listed = [line[2:].split(":", 1)[0] for line in text.splitlines() if line.startswith("- ") and ":" in line]
    listed = [name for name in listed if name.isidentifier()]
    assert listed == list(rs.Claim.model_fields)


# --- concurrency -------------------------------------------------------------------------------


def test_parallel_submits_lose_no_record(repo, work, tmp_path, capsys):
    _save(
        repo,
        [
            {"partition_id": f"new-{i}", "feature": f"feature {i}", "input_forms": ["x"], "paths": ["a.txt"]}
            for i in range(8)
        ],
    )
    dispatches = [_dispatch(repo, work, "inspector", "--partition", f"P{i + 3}", capsys=capsys) for i in range(8)]
    for d in dispatches:
        Path(d["output_path"]).write_text(json.dumps(inspector_output(["x"], [claim(input_form="x")])))
    env = {**os.environ, "TMPDIR": rs.tempfile.gettempdir()}
    procs = [
        subprocess.Popen(  # noqa: S603
            [sys.executable, str(SCRIPT), "submit", d["dispatch_id"], "--review", work.name, "--repo", str(repo)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        for d in dispatches
    ]
    for proc in procs:
        _, err = proc.communicate(timeout=60)
        assert proc.returncode == 0, err
    review = _review(work)
    assert sorted(r["record_id"] for r in review["records"]) == sorted(f"R1-{n}" for n in range(1, 9))
    state = json.loads((repo / ".review" / "review-state.json").read_text())
    assert sum(len(p["inspections"]) for p in state["partitions"]) == 8


# --- characterization: consolidation problems, the last steps, and synthesis sections ------------


def test_consolidation_problems_are_listed_in_a_fixed_order(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2"), claim(site="a.txt:3"), claim(site="a.txt:4")], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("first", "R1-1", "R1-2", "R1-3", "R1-4")])
    _inspect(repo, work, "P2", [claim(site="b.txt:1"), claim(site="b.txt:2"), claim(site="b.txt:3")], capsys)
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    output = {
        "duplicates": [
            {"record_id": "R1-5", "primary_id": "R9-9"},
            {"record_id": "R1-6", "primary_id": "R1-6"},
        ],
        "failure_modes": [mode("second", "R1-6", "R1-6", "R8-8")],
    }
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert err.splitlines()[1:] == [
        "- ids you were not given: R8-8",
        "- place each of these as a duplicate or in one failure mode: R1-7",
        "- placed more than once: R1-6",
        "- R1-5 is a duplicate of an unknown id R9-9",
        "- R1-6 cannot be a duplicate of itself",
    ]


def test_a_duplicate_of_a_record_no_consolidator_has_grouped_is_refused(repo, work, capsys):
    _inspect(repo, work, "P1", [claim()], capsys)
    d = _dispatch(repo, work, "consolidator", capsys=capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)
    output = {"duplicates": [{"record_id": "R1-1", "primary_id": "R1-2"}], "failure_modes": []}
    code, _, err = _submit(repo, work, d, output, capsys)
    assert code == 1
    assert "- R1-1 is a duplicate of R1-2, which no consolidator has grouped yet" in err.splitlines()


def _all_round_one_roles(repo, work, capsys) -> None:
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    _submitted(repo, work, keeper, {"partitions": []}, capsys)
    _round_one_lenses(repo, work, capsys)


def test_the_last_steps_lead_to_the_forms_checker_then_the_synthesizer(repo, work, capsys):
    _all_round_one_roles(repo, work, capsys)
    _inspect(repo, work, "P1", [], capsys)
    _inspect(repo, work, "P2", [], capsys)
    assert _status(repo, work, capsys)["next"] == "dispatch forms-checker"
    _check_all_forms_tested(repo, work, capsys)
    assert _status(repo, work, capsys)["next"] == "dispatch synthesizer"


def test_a_second_round_with_partitions_left_does_not_start_another(repo, work, capsys):
    _all_round_one_roles(repo, work, capsys)
    _inspect(repo, work, "P1", [], capsys)
    assert _status(repo, work, capsys)["next"].startswith("dispatch inspector --partition <partition_id>")
    d = _dispatch(repo, work, "inspector", "--partition", "P2", capsys=capsys)
    _submitted(repo, work, d, too_coarse_output(), capsys)
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    _submitted(repo, work, keeper, {"partitions": []}, capsys)
    assert _status(repo, work, capsys)["next"] == (
        "run start-round, then dispatch inspector --partition <partition_id> for each entry in pending.inspect"
    )
    _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    d = _dispatch(repo, work, "inspector", "--partition", "P2", capsys=capsys)
    output = too_coarse_output(
        input_forms=[{"input_form": FORMS[1], "status": "not checked"}], proposed_split="by kind"
    )
    _submitted(repo, work, d, output, capsys)
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    _submitted(repo, work, keeper, {"partitions": []}, capsys)
    status = _status(repo, work, capsys)
    assert status["plan_frozen"] is True
    assert "start-round" not in status["next"]
    assert "ask the user" not in status["next"]


def _challenge(repo, work, capsys, verdicts: dict[str, tuple[str, str]]) -> None:
    d = _dispatch(repo, work, "challenger", capsys=capsys)
    results = [
        {"record_id": i, "verdict": v, "strength": s, "argument": f"argument for {i}"}
        for i, (v, s) in verdicts.items()
    ]
    _submitted(repo, work, d, {"read_through": 100, "results": results}, capsys)


def _hunt_every_failure_mode(repo, work, capsys, unsupported: set[str]) -> None:
    for name, ids in _pending(repo, work, capsys)["hunt"].items():
        d = _dispatch(repo, work, "hunter", "--failure-mode", name, capsys=capsys)
        expectations = [
            {"record_id": i, "expected_supported": i not in unsupported, "reason": f"the source for {i}"} for i in ids
        ]
        records = _records(work)
        sites = [records[i]["claim"]["site"] for i in ids if i not in unsupported]
        stopped = {} if sites else {"expected": "", "searched": [], "sites": []}
        _submitted(repo, work, d, hunter_output(expectations, *sites, **stopped), capsys)


def test_a_hunter_checks_only_expectations_that_cite_a_source(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(source=None), claim(site="a.txt:2")], capsys)
    _consolidate(repo, work, capsys, failure_modes=[mode("empty values", "R1-1", "R1-2")])
    _run_all(repo, work, capsys)
    _challenge(repo, work, capsys, {"R1-1": ("upheld", "strong")})
    d = _dispatch(repo, work, "hunter", "--failure-mode", "empty values", capsys=capsys)
    assert _input(d)["check_expectations"] == ["R1-2"]
    both = [{"record_id": i, "expected_supported": True, "reason": "spec"} for i in ("R1-1", "R1-2")]
    code, _, err = _submit(repo, work, d, hunter_output(both, "a.txt:1", "a.txt:2"), capsys)
    assert code == 1
    assert "R1-1" in err
    _submitted(repo, work, d, hunter_output(both[1:], "a.txt:1", "a.txt:2"), capsys)
    records = _records(work)
    assert records["R1-1"]["hunt"] is None
    assert _verdict(work, records["R1-1"]) == "upheld"
    assert _pending(repo, work, capsys)["hunt"] == {}


def test_the_synthesizer_input_places_every_kind_of_record(repo, work, capsys):
    p1 = [
        claim(site="a.txt:1"),  # R1-1 confirmed by a run
        claim(site="a.txt:2", input=None),  # R1-2 upheld, strong
        claim(site="a.txt:3", input=None),  # R1-3 upheld, moderate
        claim(site="a.txt:4", input=None),  # R1-4 upheld, weak
        claim(site="a.txt:5"),  # R1-5 refuted by a run
        claim(site="a.txt:6", input=None),  # R1-6 disputed, then ruled refuted
        claim(site="a.txt:7", input=None),  # R1-7 disputed, left for the user
        claim(site="a.txt:8", input=None),  # R1-8 refuted by the challenger
    ]
    _inspect(repo, work, "P1", p1, capsys)
    _inspect(repo, work, "P2", [claim(site="b.txt:1")], capsys)  # R1-9 duplicate of R1-1
    adversary = _dispatch(repo, work, "test-adversary", capsys=capsys)
    _submitted(
        repo, work, adversary, {"read_through": 100, "claims": [claim(site="b.txt:5", run=run("test gap"))]}, capsys
    )
    lens = _dispatch(repo, work, "quality-lens", capsys=capsys)  # R1-11, unsupported
    _submitted(repo, work, lens, {"read_through": 100, "claims": [claim(site="b.txt:2")]}, capsys)
    _round_one_lenses(repo, work, capsys)
    _consolidate(repo, work, capsys, duplicates=[{"record_id": "R1-9", "primary_id": "R1-1"}])
    _run_all(repo, work, capsys, {"R1-5": "refuted"})
    _challenge(
        repo,
        work,
        capsys,
        {
            "R1-2": ("upheld", "strong"),
            "R1-3": ("upheld", "moderate"),
            "R1-4": ("upheld", "weak"),
            "R1-6": ("disputed", "moderate"),
            "R1-7": ("disputed", "weak"),
            "R1-8": ("refuted", "strong"),
        },
    )
    _ok(repo, "rule", "R1-6", "--review", work.name, "--verdict", "refuted", "--reason", "intended", capsys=capsys)
    _hunt_every_failure_mode(repo, work, capsys, unsupported={"R1-11"})
    _check_all_forms_tested(repo, work, capsys)
    data = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))

    findings = {f["record_id"]: f for f in data["findings"]}
    assert {i: (f["verdict"], f["confidence"]) for i, f in findings.items()} == {
        "R1-1": ("confirmed", "high"),
        "R1-2": ("upheld", "high"),
        "R1-3": ("upheld", "medium"),
        "R1-4": ("upheld", "low"),
    }
    assert findings["R1-1"]["corroborated"] is True
    assert findings["R1-1"]["roles"] == ["inspector"]
    assert findings["R1-2"]["corroborated"] is False
    assert [d["record_id"] for d in data["disputed"]] == ["R1-7"]
    assert [t["record_id"] for t in data["test_gaps"]] == ["R1-10"]
    assert {d["record_id"]: (d["verdict"], d["reason"]) for d in data["dropped"]} == {
        "R1-5": ("refuted", "the probe's result matched the expected result: ok"),
        "R1-6": ("refuted", "user ruling: intended"),
        "R1-8": ("refuted", "argument for R1-8"),
        "R1-9": ("duplicate", "duplicate of R1-1"),
        "R1-11": ("unsupported", "the source for R1-11"),
    }
    assert data["merge_readiness"] == "no"
    assert data["blocking_record_ids"] == ["R1-1", "R1-2", "R1-3", "R1-4"]
    assert [i["partition_id"] for i in data["inspections"]] == ["P1", "P2"]


def test_a_review_without_checks_is_unverified(repo, work, tmp_path, capsys):
    work = _start(repo, tmp_path, capsys, base="no checks")
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [claim(introduced="pre-existing")], capsys)
    _inspect(repo, work, "P2", [], capsys)
    _consolidate(repo, work, capsys)
    _run_all(repo, work, capsys)
    _hunt_every_failure_mode(repo, work, capsys, unsupported=set())
    _check_all_forms_tested(repo, work, capsys)
    data = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))
    assert data["merge_readiness"] == "unverified"
    assert data["blocking_record_ids"] == []


# --- the frozen plan, and the finished review -------------------------------------------------


def test_a_converged_round_freezes_the_plan_and_finishes_its_own_work(repo, work, capsys):
    _finish_round_one(repo, work, capsys)
    _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    claims = [claim(input_form="a value of only spaces"), claim(site="a.txt:9", input_form="a value of only spaces")]
    _submitted(repo, work, d, inspector_output(_input(d)["pending_input_forms"], claims), capsys)
    coarse = _dispatch(repo, work, "inspector", "--partition", "P2", capsys=capsys)
    _submitted(repo, work, coarse, too_coarse_output(), capsys)
    _consolidate(
        repo,
        work,
        capsys,
        duplicates=[{"record_id": "R2-1", "primary_id": "R1-1"}],
        failure_modes=[mode("mode R1-1", "R2-2")],
    )
    status = _status(repo, work, capsys)
    assert status["plan_frozen"] is True
    code, _, err = _cli(repo, "start-round", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "frozen" in err

    _run_all(repo, work, capsys)
    hunter = _dispatch(repo, work, "hunter", "--failure-mode", "mode R1-1", capsys=capsys)
    output = hunter_output(
        [{"record_id": "R2-2", "expected_supported": True, "reason": "spec"}],
        "a.txt:9",
        suspected_input_forms=["a value of only tabs"],
    )
    _submitted(repo, work, hunter, output, capsys)
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    assert _input(keeper)["plan_frozen"] is True
    forms = [*FORMS, "a value of only spaces", "a value of only tabs"]
    partitions = [
        {"partition_id": "P1", "feature": "values of a", "origin": "spec", "input_forms": forms, "paths": ["a.txt"]},
        {"partition_id": "P2", "feature": "values of b", "child_ids": ["new-1", "new-2"]},
        {"partition_id": "new-1", "feature": "empty values of b", "input_forms": [FORMS[0]], "paths": ["b.txt"]},
        {"partition_id": "new-2", "feature": "repeated values of b", "input_forms": [FORMS[1]], "paths": ["b.txt"]},
    ]
    _submitted(repo, work, keeper, {"partitions": partitions, "changes": ["P1: new form", "P2: split"]}, capsys)

    status = _status(repo, work, capsys)
    assert [n["partition_id"] for n in status["pending"]["inspect"]] == ["P4"]
    assert status["next"].startswith("dispatch inspector --partition <partition_id>")
    _inspect(repo, work, "P4", [], capsys)
    status = _status(repo, work, capsys)
    assert status["pending"]["inspect"] == []
    assert status["next"] == "dispatch forms-checker"
    unfrozen = _ok(repo, "status", "--scope", "staged", capsys=capsys)["pending"]["inspect"]
    assert [n["partition_id"] for n in unfrozen] == ["P1"]


def test_submitting_the_report_records_the_finished_review(repo, work, capsys):
    _judged_review(repo, work, capsys)
    report = repo / ".review" / "code-review-test.md"
    d = _dispatch(repo, work, "synthesizer", "--report", str(report), capsys=capsys)
    assert "forms_carried_forward" not in _input(d)
    _submitted(repo, work, d, "# Report\n\n- R1-1: an empty value is accepted\n", capsys)
    previous = _ok(repo, "status", "--scope", "staged", capsys=capsys)["previous_review"]
    assert previous["review_id"] == work.name
    assert previous["head"] == _review(work)["head"]
    assert previous["report"] == str(report)
    assert previous["report_exists"] is True
    with pytest.raises(SystemExit):
        rs.main(["record-run", "--scope", "staged", "--report", str(report), "--repo", str(repo)])


def _finish(repo, work, capsys) -> dict:
    d = _dispatch(repo, work, "synthesizer", capsys=capsys)
    data = _input(d)
    ids = [v["record_id"] for key in ("findings", "disputed", "test_gaps", "dropped") for v in data[key]]
    _submitted(repo, work, d, "# Report\n\n" + "".join(f"- {i}\n" for i in ids), capsys)
    return data


def _second_review(repo, tmp_path, capsys) -> Path:
    return _start(repo, tmp_path, capsys, "--passed-checks", "uv run pytest", base="second review")


def _finish_without_new_records(repo, work, capsys) -> dict:
    _round_one_lenses(repo, work, capsys)
    _check_all_forms_tested(repo, work, capsys)
    return _finish(repo, work, capsys)


def test_a_blocker_on_unchanged_files_keeps_its_verdict_in_the_next_review(repo, work, tmp_path, capsys):
    _judged_review(repo, work, capsys)
    assert _finish(repo, work, capsys)["blocking_record_ids"] == ["R1-1"]
    second = _second_review(repo, tmp_path, capsys)
    carried = _records(second)["R1-1"]
    assert carried["carried_from"] == {"review_id": work.name, "record_id": "R1-1", "files_unchanged": True}
    assert _verdict(second, carried) == "confirmed"
    pending = _pending(repo, second, capsys)
    assert (pending["inspect"], pending["consolidate"], pending["run"], pending["hunt"]) == ([], [], [], {})
    data = _finish_without_new_records(repo, second, capsys)
    assert data["merge_readiness"] == "no"
    assert data["blocking_record_ids"] == ["R1-1"]
    assert data["findings"][0]["carried_from"]["review_id"] == work.name


def test_a_blocker_on_changed_files_is_judged_again(repo, work, tmp_path, capsys):
    _judged_review(repo, work, capsys)
    _finish(repo, work, capsys)
    (repo / "a.txt").write_text("fixed a\n")
    _git(repo, "add", "a.txt")
    second = _second_review(repo, tmp_path, capsys)
    carried = _records(second)["R1-1"]
    assert carried["carried_from"]["files_unchanged"] is False
    assert carried["claim"]["run"] is None
    assert carried["run"] is None
    assert _pending(repo, second, capsys)["consolidate"] == ["R1-1"]


def test_a_missing_previous_review_leaves_merge_readiness_unverified(repo, work, tmp_path, capsys):
    _judged_review(repo, work, capsys)
    _finish(repo, work, capsys)
    for path in sorted(work.rglob("*"), reverse=True):
        path.unlink() if path.is_file() else path.rmdir()
    work.rmdir()
    second = _second_review(repo, tmp_path, capsys)
    data = _finish_without_new_records(repo, second, capsys)
    assert data["missing_previous_review"] == work.name
    assert data["merge_readiness"] == "unverified"


def test_status_reports_a_finished_review(repo, work, capsys):
    _judged_review(repo, work, capsys)
    report = repo / ".review" / "code-review-test.md"
    d = _dispatch(repo, work, "synthesizer", "--report", str(report), capsys=capsys)
    _submitted(repo, work, d, "# Report\n\n- R1-1: an empty value is accepted\n", capsys)
    assert _status(repo, work, capsys)["next"] == f"the review is finished; present the report at {report}"


def test_synthesis_waits_for_partitions_this_review_still_inspects(repo, work, capsys):
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [], capsys)
    code, _, err = _cli(repo, "dispatch", "synthesizer", "--review", work.name, capsys=capsys)
    assert code == 1
    assert '"inspect"' in err


def test_the_submit_command_keeps_an_explicit_review_dir(repo, tmp_path, capsys):
    custom = tmp_path / "custom-review-dir"
    packet = str(_packet_json(repo, tmp_path))
    argv = ["start-review", "--scope", "staged", "--packet-json", packet, "--review-dir", str(custom), *VALUES]
    review_id = _ok(repo, *argv, capsys=capsys)["review_id"]
    data = _ok(repo, "dispatch", "security-lens", "--review", review_id, "--review-dir", str(custom), capsys=capsys)
    work = custom / "reviews" / review_id
    d = _input(_review_dispatch(work, data["dispatches"][0]["dispatch_id"]))
    Path(d["output_path"]).write_text(json.dumps({"read_through": 100}))
    command = shlex.split(d["submit_command"])
    assert rs.main(command[1:]) == 0
    assert json.loads(capsys.readouterr().out)["already_submitted"] is False


# --- pressure-test regressions ----------------------------------------------------------------


def test_next_keeps_naming_inspectors_until_every_partition_is_inspected(repo, work, capsys):
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    _submitted(repo, work, keeper, {"partitions": []}, capsys)
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [claim()], capsys)
    assert _status(repo, work, capsys)["next"].startswith("dispatch inspector --partition <partition_id>")
    _inspect(repo, work, "P2", [], capsys)
    assert _status(repo, work, capsys)["next"] == "dispatch consolidator"


def test_a_round_converges_only_after_every_partition_is_inspected(repo, work, capsys):
    _finish_round_one(repo, work, capsys)
    _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    claims = [claim(input_form="a value of only spaces"), claim(site="a.txt:9", input_form="a value of only spaces")]
    _submitted(repo, work, d, inspector_output(_input(d)["pending_input_forms"], claims), capsys)
    _consolidate(
        repo,
        work,
        capsys,
        duplicates=[{"record_id": "R2-1", "primary_id": "R1-1"}],
        failure_modes=[mode("mode R1-1", "R2-2")],
    )
    status = _status(repo, work, capsys)
    assert status["plan_frozen"] is False
    assert [n["partition_id"] for n in status["pending"]["inspect"]] == ["P2"]
    _inspect(repo, work, "P2", [], capsys)
    assert _status(repo, work, capsys)["plan_frozen"] is True


def test_a_split_of_the_repeat_that_converged_unfreezes_the_plan(repo, work, capsys, monkeypatch):
    monkeypatch.setattr(rs, "MAX_ROUNDS", 3)
    _round_one_lenses(repo, work, capsys)
    _inspect(repo, work, "P1", [claim()], capsys)
    _inspect(repo, work, "P2", [], capsys)
    _consolidate(repo, work, capsys)
    _run_all(repo, work, capsys, {"R1-1": "refuted"})
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    part = {
        "partition_id": "P1",
        "feature": "values of a",
        "origin": "spec",
        "input_forms": [*FORMS, "a value of only spaces"],
        "paths": ["a.txt"],
    }
    _submitted(repo, work, keeper, {"partitions": [part]}, capsys)
    _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    _inspect(repo, work, "P1", [claim(input_form="a value of only spaces")], capsys)
    _consolidate(repo, work, capsys, duplicates=[{"record_id": "R2-1", "primary_id": "R1-1"}])
    assert _status(repo, work, capsys)["plan_frozen"] is True
    result = _run_all(repo, work, capsys)
    assert result["split_record_ids"] == ["R2-1"]
    status = _status(repo, work, capsys)
    assert status["convergence"]["converged"] is False
    assert status["plan_frozen"] is False


def test_a_runner_dispatched_again_with_the_same_records_returns_the_open_one(repo, work, capsys):
    _inspect(repo, work, "P1", [claim(), claim(site="a.txt:2")], capsys)
    _consolidate(repo, work, capsys)
    _dispatch(repo, work, "runner", "--records", "R1-1", capsys=capsys)
    second = _dispatch(repo, work, "runner", "--records", "R1-1", "R1-2", capsys=capsys)
    assert [r["record_id"] for r in _input(second)["records"]] == ["R1-2"]
    again = _dispatch(repo, work, "runner", "--records", "R1-1", "R1-2", capsys=capsys)
    assert again == second | {"already_dispatched": True}


def test_round_one_roles_must_run_before_a_round_ends_or_synthesis_starts(repo, work, capsys):
    keeper = _dispatch(repo, work, "keeper", capsys=capsys)
    _submitted(repo, work, keeper, {"partitions": []}, capsys)
    _inspect(repo, work, "P1", [], capsys)
    _inspect(repo, work, "P2", [], capsys)
    code, _, err = _cli(repo, "start-round", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "security-lens" in err
    code, _, err = _cli(repo, "dispatch", "synthesizer", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "security-lens" in err


# --- the review's values, filled prompts, and dispatching a whole step --------------------


def _built(repo: Path, work: Path, capsys, components: tuple[str, ...] = ("a",)) -> None:
    """Dispatch and submit one list builder per component, then the keeper."""
    for name in components:
        d = _dispatch(repo, work, "list-builder", "--component", name, "--paths", f"{name}.txt", capsys=capsys)
        _submitted(repo, work, d, {"read_through": 100, "proposals": []}, capsys)
    _submitted(repo, work, _dispatch(repo, work, "keeper", capsys=capsys), {"partitions": []}, capsys)


def _step(repo: Path, work: Path, *extra: str, capsys) -> dict:
    """Dispatch with no role: register what the next step names."""
    return _ok(repo, "dispatch", "--review", work.name, *extra, capsys=capsys)


def _record(repo: Path, work: Path, entry: dict, output: dict, capsys) -> dict:
    """Submit the output of a dispatch that a role-less dispatch registered."""
    return _submitted(repo, work, _review_dispatch(work, entry["dispatch_id"]), output, capsys)


def _prompt(work: Path, role: str, component: str = "") -> str:
    review = rs.read_review(work)
    d = rs._new_dispatch(review, role, work)
    d.component = component
    return rs.render_prompt(review, d)


def test_the_test_adversary_of_a_standard_review_gets_the_flagged_claims(repo, standard_work, capsys):
    flagged = "parse SHALL reject every malformed header; tests use only the scenario headers"
    _ok(repo, "update-review", "--review", standard_work.name, "--flagged-claims", flagged, capsys=capsys)
    assert flagged in _prompt(standard_work, "test-adversary")


def test_start_review_needs_the_intent_and_how_to_run(repo, tmp_path, capsys):
    path = str(_packet_json(repo, tmp_path))
    argv = ["start-review", "--scope", "staged", "--packet-json", path, "--repo", str(repo)]
    with pytest.raises(SystemExit):
        rs.main(argv)
    capsys.readouterr()
    code, _, err = _cli(repo, *argv[:-2], "--intent", " ", "--how-to-run", "uv run pytest", capsys=capsys)
    assert code == 1
    assert "--intent" in err


def test_dispatch_writes_the_filled_prompt(repo, work, capsys):
    d = _dispatch(repo, work, "inspector", "--partition", "P1", capsys=capsys)
    prompt = Path(d["prompt_path"]).read_text()
    assert "- site:" in prompt
    assert prompt.rstrip().endswith(d["input_path"])
    assert "{{" not in prompt
    assert "```" not in prompt


@pytest.mark.parametrize("role", rs.ROLES)
def test_every_role_prompt_fills_every_slot(repo, work, capsys, role):
    _update(repo, work, "--architecture", "yes", capsys=capsys)
    prompt = _prompt(work, role)
    for leftover in ("{{", "}}", "<input_path>", "paste assets", "<orchestrator", "<..."):
        assert leftover not in prompt
    assert f"-{role}.json" in prompt


def test_probe_roles_get_how_to_run_and_lenses_get_the_intent(repo, work, capsys):
    assert "uv run pytest tests/" in _prompt(work, "runner")
    lens = _prompt(work, "security-lens")
    assert "reject empty values" in lens
    assert "pre-commit" in lens


def test_architecture_section_goes_only_on_the_lens_with_no_component(repo, work, capsys):
    without = _prompt(work, "quality-lens")
    _update(repo, work, "--architecture", "yes", capsys=capsys)
    assert "## Architecture" not in without
    assert "## Architecture" in _prompt(work, "quality-lens")
    assert "Test 3" in _prompt(work, "quality-lens")
    assert "## Architecture" not in _prompt(work, "quality-lens", component="a")


def test_domain_checks_file_reaches_the_security_lens(repo, work, tmp_path, capsys):
    checks = tmp_path / "checks.md"
    checks.write_text("- every query is parameterized\n")
    _update(repo, work, "--domain-checks-file", str(checks), capsys=capsys)
    prompt = _prompt(work, "security-lens")
    assert "## Domain-specific checks" in prompt
    assert "every query is parameterized" in prompt


def test_update_review_changes_later_prompts_and_records_the_update(repo, work, capsys):
    data = _update(repo, work, "--how-to-run", "cargo test --offline", capsys=capsys)
    assert data["updated"] == ["how_to_run"]
    assert data["already_updated"] is False
    assert "cargo test --offline" in _prompt(work, "runner")
    (update,) = _review(work)["updates"]
    assert update["values"] == {"how_to_run": "cargo test --offline"}


def test_update_review_again_with_the_same_values_changes_nothing(repo, work, capsys):
    _update(repo, work, "--how-to-run", "cargo test --offline", capsys=capsys)
    again = _update(repo, work, "--how-to-run", "cargo test --offline", capsys=capsys)
    assert again["updated"] == []
    assert again["already_updated"] is True
    assert len(_review(work)["updates"]) == 1


def test_update_review_needs_a_value(repo, work, capsys):
    code, _, err = _cli(repo, "update-review", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "--how-to-run" in err


def test_the_synthesizer_input_lists_the_updates(repo, work, capsys):
    _update(repo, work, "--how-to-run", "cargo test --offline", capsys=capsys)
    for partition_id in ("P1", "P2"):
        _inspect(repo, work, partition_id, [], capsys)
    data = _finish_without_new_records(repo, work, capsys)
    assert data["updates"][0]["values"] == {"how_to_run": "cargo test --offline"}


def test_several_components_with_architecture_need_one_more_quality_lens(repo, work, capsys):
    _update(repo, work, "--architecture", "yes", capsys=capsys)
    _built(repo, work, capsys, components=("a", "b"))
    entries = _step(repo, work, capsys=capsys)["dispatches"]
    lenses = [d["description"] for d in entries if d["role"] == "quality-lens"]
    assert lenses == ["quality-lens: a", "quality-lens: b", "quality-lens"]


def test_dispatch_with_one_role_and_with_none_print_the_same_shape(repo, work, capsys):
    _built(repo, work, capsys)
    one = _ok(repo, "dispatch", "security-lens", "--review", work.name, capsys=capsys)
    step = _step(repo, work, "--limit", "2", capsys=capsys)
    assert (
        set(one) == set(step) == {"dispatches", "open_dispatches", "next", "already_dispatched", "deferred", "rulings"}
    )
    assert set(one["dispatches"][0]) == set(step["dispatches"][0]) == set(step["open_dispatches"][0])
    assert _status(repo, work, capsys)["open_dispatches"] == step["open_dispatches"]


def test_dispatch_with_no_role_refuses_a_role_option(repo, work, capsys):
    code, _, err = _cli(repo, "dispatch", "--review", work.name, "--partition", "P1", capsys=capsys)
    assert code == 1
    assert "--partition" in err
    assert "role" in err


def test_dispatch_with_no_role_names_the_step_it_cannot_take(repo, work, capsys):
    data = _step(repo, work, capsys=capsys)
    assert data["dispatches"] == []
    assert data["next"] == "dispatch list-builder for each component"


def test_dispatch_with_no_role_registers_round_one_up_to_the_limit(repo, work, capsys):
    _built(repo, work, capsys)
    data = _step(repo, work, "--limit", "3", capsys=capsys)
    assert [d["role"] for d in data["dispatches"]] == ["inspector", "inspector", "quality-lens"]
    assert [d["model"] for d in data["dispatches"]] == ["small", "small", "strong"]
    for d in data["dispatches"]:
        assert Path(d["prompt_path"]).is_file()
        assert d["description"]
    rest = _step(repo, work, "--limit", "8", capsys=capsys)
    assert [d["role"] for d in rest["dispatches"]] == ["security-lens", "test-adversary", "spec-lens"]
    assert len(rest["open_dispatches"]) == 6


def test_dispatch_with_no_role_registers_nothing_at_the_limit(repo, work, capsys):
    _built(repo, work, capsys)
    first = _step(repo, work, "--limit", "2", capsys=capsys)
    again = _step(repo, work, "--limit", "2", capsys=capsys)
    assert again["dispatches"] == []
    assert again["open_dispatches"] == first["dispatches"]
    assert again["next"].startswith("wait for the open dispatches")


def test_dispatch_with_no_role_waits_for_the_step_before_judging(repo, work, capsys):
    _built(repo, work, capsys)
    batch = _step(repo, work, capsys=capsys)["dispatches"]
    inspectors = [d for d in batch if d["role"] == "inspector"]
    _record(repo, work, inspectors[0], inspector_output(FORMS, [claim()]), capsys)
    assert _step(repo, work, capsys=capsys)["dispatches"] == []
    _record(repo, work, inspectors[1], inspector_output(FORMS, []), capsys)
    for d in batch:
        if d["role"] != "inspector":
            _record(repo, work, d, {"read_through": 100}, capsys)
    judged = _step(repo, work, capsys=capsys)
    assert [d["role"] for d in judged["dispatches"]] == ["consolidator"]


def test_dispatch_with_no_role_gives_each_runner_a_few_records(repo, work, capsys):
    _built(repo, work, capsys)
    batch = _step(repo, work, capsys=capsys)["dispatches"]
    claims = [claim(input=f"'{n}'", site=f"a.txt:{n}") for n in range(1, 6)]
    inspectors = [d for d in batch if d["role"] == "inspector"]
    _record(repo, work, inspectors[0], inspector_output(FORMS, claims), capsys)
    _record(repo, work, inspectors[1], inspector_output(FORMS, []), capsys)
    for d in batch:
        if d["role"] != "inspector":
            _record(repo, work, d, {"read_through": 100}, capsys)
    _consolidate(repo, work, capsys)
    runners = _step(repo, work, capsys=capsys)["dispatches"]
    sizes = [len(_input(_review_dispatch(work, d["dispatch_id"]))["records"]) for d in runners]
    assert [d["role"] for d in runners] == ["runner", "runner"]
    assert sizes == [3, 2]


def _disputed_review(repo, work, capsys) -> None:
    """Finish every step of a review whose one record the challenger left disputed."""
    _all_round_one_roles(repo, work, capsys)
    _inspect(repo, work, "P1", [claim(input=None)], capsys)
    _inspect(repo, work, "P2", [], capsys)
    _consolidate(repo, work, capsys)
    _challenge(repo, work, capsys, {"R1-1": ("disputed", "moderate")})
    _check_all_forms_tested(repo, work, capsys)


def test_dispatch_with_no_role_stops_for_the_ruling_on_a_disputed_record(repo, work, capsys):
    _disputed_review(repo, work, capsys)
    step = _step(repo, work, capsys=capsys)
    assert step["dispatches"] == []
    assert "rule <record_id> --review <review_id> --verdict" in step["next"]
    assert "R1-1" in step["next"]
    assert _status(repo, work, capsys)["next"] == step["next"]


def test_a_disputed_record_that_could_not_block_is_reported_without_a_ruling(repo, standard_work, capsys):
    _standard_lens_claims(repo, standard_work, capsys, claim(priority="medium"))
    _consolidate(repo, standard_work, capsys)
    _challenge(repo, standard_work, capsys, {"R1-1": ("disputed", "moderate")})
    status = _status(repo, standard_work, capsys)
    assert status["pending"]["rule"] == []
    assert status["next"] == "dispatch synthesizer"


def test_a_disputed_record_of_high_priority_needs_a_ruling_even_when_it_is_pre_existing(repo, standard_work, capsys):
    _standard_lens_claims(repo, standard_work, capsys, claim(introduced="pre-existing"))
    _consolidate(repo, standard_work, capsys)
    _challenge(repo, standard_work, capsys, {"R1-1": ("disputed", "moderate")})
    assert _pending(repo, standard_work, capsys)["rule"] == ["R1-1"]


def test_dispatch_shows_each_disputed_record_that_needs_a_ruling(repo, work, capsys):
    _disputed_review(repo, work, capsys)
    (ruling,) = _step(repo, work, capsys=capsys)["rulings"]
    assert ruling["record_id"] == "R1-1"
    assert ruling["claim"]["observation"] == "an empty value is accepted"
    assert ruling["argument"] == "argument for R1-1"


def test_dispatch_names_the_roles_the_limit_held_back(repo, standard_work, capsys):
    data = _ok(repo, "dispatch", "--review", standard_work.name, "--limit", "2", capsys=capsys)
    assert len(data["dispatches"]) == 2
    assert data["deferred"] == ["test-adversary", "spec-lens"]


def test_status_lists_only_the_unfinished_reviews_of_this_branch(repo, standard_work, capsys):
    _git(repo, "checkout", "-q", "-b", "other")
    assert _ok(repo, "status", "--scope", "staged", capsys=capsys)["unfinished_reviews"] == []


def test_the_synthesizer_is_told_which_role_found_each_record(repo, standard_work, capsys):
    lens = _dispatch(repo, standard_work, "spec-lens", capsys=capsys)
    _submitted(
        repo, standard_work, lens, {"read_through": 100, "claims": [claim()], "summary": "partial, 1 gap"}, capsys
    )
    _round_one_lenses(repo, standard_work, capsys)
    _consolidate(repo, standard_work, capsys)
    _challenge(repo, standard_work, capsys, {"R1-1": ("upheld", "strong")})
    data = _input(_dispatch(repo, standard_work, "synthesizer", capsys=capsys))
    (finding,) = data["findings"]
    assert finding["role"] == "spec-lens"


def test_a_spec_given_to_the_review_gets_the_spec_lens_without_a_source_of_truth(repo, work, tmp_path, capsys):
    other = _start(repo, tmp_path, capsys, "--spec", "docs/prd-42.md", has_source_of_truth=False, base="no source")
    _built(repo, other, capsys)
    roles = [d["role"] for d in _step(repo, other, capsys=capsys)["dispatches"]]
    assert "spec-lens" in roles
    assert "Spec/ticket/PRD: docs/prd-42.md" in _prompt(other, "spec-lens")


def test_a_spec_lens_with_no_source_of_truth_and_no_spec_is_refused(repo, work, tmp_path, capsys):
    other = _start(repo, tmp_path, capsys, has_source_of_truth=False, base="no source")
    _built(repo, other, capsys)
    assert "spec-lens" not in [d["role"] for d in _step(repo, other, capsys=capsys)["dispatches"]]
    code, _, err = _cli(repo, "dispatch", "spec-lens", "--review", other.name, capsys=capsys)
    assert code == 1
    assert "update-review --review <review_id> --spec" in err


def test_a_forms_checker_is_refused_while_judging_is_unfinished(repo, work, capsys):
    _all_round_one_roles(repo, work, capsys)
    _inspect(repo, work, "P1", [claim()], capsys)
    _inspect(repo, work, "P2", [], capsys)
    _consolidate(repo, work, capsys)
    code, _, err = _cli(repo, "dispatch", "forms-checker", "--review", work.name, capsys=capsys)
    assert code == 1
    assert '"run": ["R1-1"]' in err


def test_a_forms_checker_is_refused_while_partitions_wait_for_inspection(repo, work, capsys):
    _all_round_one_roles(repo, work, capsys)
    _inspect(repo, work, "P1", [], capsys)
    code, _, err = _cli(repo, "dispatch", "forms-checker", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "P2" in err


def test_an_inspector_after_the_keeper_refined_the_list_waits_for_the_next_round(repo, work, capsys):
    _finish_round_one(repo, work, capsys)
    code, _, err = _cli(repo, "dispatch", "inspector", "--partition", "P2", "--review", work.name, capsys=capsys)
    assert code == 1
    assert "start-round --review <review_id>" in err
    _ok(repo, "start-round", "--review", work.name, capsys=capsys)
    _dispatch(repo, work, "inspector", "--partition", "P2", capsys=capsys)


CHANGES = {
    "update-review": ("update-review", "--how-to-run", "cargo test --offline"),
    "rule": ("rule", "R1-1", "--verdict", "upheld", "--reason", "the spec is clear"),
    "start-round": ("start-round",),
    "dispatch": ("dispatch", "security-lens"),
}


@pytest.mark.parametrize("command", CHANGES)
def test_a_review_takes_no_change_while_the_synthesizer_writes_the_report(repo, work, capsys, command):
    _disputed_review(repo, work, capsys)
    _dispatch(repo, work, "synthesizer", capsys=capsys)
    before = _review(work)
    code, _, err = _cli(repo, *CHANGES[command], "--review", work.name, capsys=capsys)
    assert code == 1
    assert "the synthesizer is writing the report" in err
    assert _review(work) == before


@pytest.mark.parametrize("command", [*CHANGES, "synthesizer"])
def test_a_finished_review_takes_no_change(repo, work, capsys, command):
    _disputed_review(repo, work, capsys)
    _finish(repo, work, capsys)
    before = _review(work)
    argv = CHANGES.get(command, ("dispatch", "synthesizer"))
    code, _, err = _cli(repo, *argv, "--review", work.name, capsys=capsys)
    assert code == 1
    assert "the review is finished" in err
    assert _review(work) == before


def test_a_finished_review_still_answers_a_repeated_command(repo, work, capsys):
    _disputed_review(repo, work, capsys)
    rule = ("rule", "R1-1", "--review", work.name, "--verdict", "refuted", "--reason", "intended")
    _ok(repo, *rule, capsys=capsys)
    synthesizer = _dispatch(repo, work, "synthesizer", capsys=capsys)
    assert _dispatch(repo, work, "synthesizer", capsys=capsys)["already_dispatched"] is True
    _submitted(repo, work, synthesizer, "# Report\n\n- R1-1\n", capsys)
    assert _ok(repo, *rule, capsys=capsys)["already_ruled"] is True
    assert _update(repo, work, *VALUES, capsys=capsys)["already_updated"] is True


def test_a_synthesizer_given_no_report_path_writes_a_named_report_in_the_review_directory(repo, work, capsys):
    _partition_loop_stopped(repo, work, capsys)
    _check_all_forms_tested(repo, work, capsys)
    (entry,) = _step(repo, work, capsys=capsys)["dispatches"]
    report = Path(_review_dispatch(work, entry["dispatch_id"])["output_path"])
    assert entry["role"] == "synthesizer"
    assert report.parent == (repo / ".review").resolve()
    assert report.match(
        "code-review-[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9]-staged.md"
    )
    _record(repo, work, entry, "# Report\n", capsys)
    assert _status(repo, work, capsys)["next"] == f"the review is finished; present the report at {report}"


def test_dispatch_with_no_role_passes_the_report_path_to_the_synthesizer(repo, work, capsys):
    _partition_loop_stopped(repo, work, capsys)
    _check_all_forms_tested(repo, work, capsys)
    report = repo / ".review" / "code-review-named.md"
    (entry,) = _step(repo, work, "--report", str(report), capsys=capsys)["dispatches"]
    assert _review_dispatch(work, entry["dispatch_id"])["output_path"] == str(report.resolve())


def _five_records_to_run(repo, work, capsys) -> None:
    _all_round_one_roles(repo, work, capsys)
    claims = [claim(input=f"'{n}'", site=f"a.txt:{n}") for n in range(1, 6)]
    _inspect(repo, work, "P1", claims, capsys)
    _inspect(repo, work, "P2", [], capsys)
    _consolidate(repo, work, capsys)


def test_a_runner_given_a_record_that_does_not_wait_is_refused(repo, work, capsys):
    _five_records_to_run(repo, work, capsys)
    argv = ("dispatch", "runner", "--records", "R1-1", "R1-99", "--review", work.name)
    code, _, err = _cli(repo, *argv, capsys=capsys)
    assert code == 1
    assert "R1-99" in err
    assert "R1-1 " not in err
    assert _review(work)["dispatches"][-1]["role"] != "runner"
    _dispatch(repo, work, "runner", "--records", "R1-1", capsys=capsys)
    code, _, err = _cli(repo, *argv, capsys=capsys)
    assert code == 1
    assert "R1-99" in err


def test_next_sends_the_runners_and_challengers_through_dispatch_with_no_role(repo, work, capsys):
    _five_records_to_run(repo, work, capsys)
    assert _status(repo, work, capsys)["next"].startswith("dispatch --review <review_id>, with no role")
    _run_all(repo, work, capsys, dict.fromkeys(["R1-1"], "not runnable"))
    assert _status(repo, work, capsys)["next"].startswith("dispatch --review <review_id>, with no role")
    assert _pending(repo, work, capsys)["challenge"] == ["R1-1"]


def test_a_list_builder_given_a_file_the_packet_does_not_change_is_refused(repo, work, capsys):
    argv = ("dispatch", "list-builder", "--component", "a", "--paths", "a.txt", "c.txt", "--review", work.name)
    code, _, err = _cli(repo, *argv, capsys=capsys)
    assert code == 1
    assert "c.txt" in err
    assert "a.txt, b.txt" in err


def test_the_hunter_prompt_names_every_output_field_and_site_status(repo, work, capsys):
    prompt = _prompt(work, "hunter")
    output = prompt.split("## Output")[1]
    for field in (*rs.HunterOutput.model_fields, *rs.HuntSite.model_fields):
        assert f'"{field}"' in output, field
    for status in ("handled", "claims", "not checked"):
        assert f"`{status}`" in prompt, status
    assert "(scopes `staged`, `branch`, `worktree`)" in prompt


@pytest.mark.parametrize("role", ["consolidator", "synthesizer"])
def test_the_roles_that_read_a_hunt_are_told_its_fields(repo, work, capsys, role):
    prompt = _prompt(work, role)
    for field in ("expected", "searched", "sites"):
        assert field in prompt, field
    assert "`not checked`" in prompt or "`handled`" in prompt


@pytest.mark.parametrize("role", ["hunter", "consolidator", "synthesizer"])
def test_the_roles_that_write_or_read_misgrouped_are_told_of_it(repo, work, capsys, role):
    prompt = _prompt(work, role)
    task, output = prompt.split("## Output")[0], prompt.split("## Output")[1]
    assert "misgrouped" in task
    if role == "hunter":
        assert '"misgrouped": [{"record_id", "reason"}]' in output
        assert "largest group of records that break one rule" in task


@pytest.mark.parametrize(
    "role", ["hunter", "challenger", "spec-lens", "test-adversary", "list-builder", "inspector", "forms-checker"]
)
def test_the_roles_that_check_a_cited_source_are_told_where_the_spec_is(repo, work, capsys, role):
    assert "Spec/ticket/PRD: in the packet" in _prompt(work, role)
    _update(repo, work, "--spec", "/abs/spec.md", capsys=capsys)
    assert "Spec/ticket/PRD: /abs/spec.md" in _prompt(work, role)


def test_a_disputed_record_left_unruled_is_reported_by_the_synthesizer(repo, work, capsys):
    _disputed_review(repo, work, capsys)
    data = _input(_dispatch(repo, work, "synthesizer", capsys=capsys))
    assert [v["record_id"] for v in data["disputed"]] == ["R1-1"]


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    raise SystemExit(pytest.main([__file__, "-q", "--rootdir", here, "--confcutdir", here]))
