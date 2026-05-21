#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "markdown-it-py>=3.0",
#   "pytest>=8.0.0",
# ]
# ///
"""Regression tests for check_modified_completeness.py.

Behavior-level: each test builds a specs tree in a tmp dir, calls main(argv),
and asserts the exit code and key output. Parser-agnostic by design.

Run: uv run tests/sdd/test_check_modified_completeness.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "skills" / "sdd" / "scripts" / "check_modified_completeness.py"
_spec = importlib.util.spec_from_file_location("check_modified_completeness", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None
cmc = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = cmc
_spec.loader.exec_module(cmc)


# --- fixtures / helpers ------------------------------------------------------


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _baseline(root: Path, capability: str, body: str) -> None:
    _write(root / "specs" / capability / "spec.md", body)


def _delta(root: Path, change: str, capability: str, body: str) -> None:
    _write(root / "changes" / change / "specs" / capability / "spec.md", body)


def _scenario(name: str) -> str:
    return f"#### Scenario: {name}\n\n- **GIVEN** g\n- **WHEN** w\n- **THEN** t\n"


def _baseline_body(req: str, *scenarios: str) -> str:
    body = f"# Spec\n\n## Purpose\n\np.\n\n## Requirements\n\n### Requirement: {req}\n\nThe system SHALL x.\n\n"
    return body + "\n".join(_scenario(s) for s in scenarios)


def _delta_body(req: str, *scenarios: str, previously: bool = True, allow: str | None = None) -> str:
    body = "# Delta\n\n## MODIFIED Requirements\n\n"
    body += f"### Requirement: {req}\n\n"
    if previously:
        body += "> Previously: did more\n\n"
    if allow:
        body += f"<!-- modified-removes: {allow} -->\n\n"
    body += "The system SHALL x better.\n\n"
    body += "\n".join(_scenario(s) for s in scenarios)
    return body


# --- core contract -----------------------------------------------------------


def test_dropped_scenario__fails_with_exit_1(tmp_path, capsys):
    _baseline(tmp_path, "alpha", _baseline_body("Foo", "ScenA", "ScenB"))
    _delta(tmp_path, "c", "alpha", _delta_body("Foo", "ScenA"))

    rc = cmc.main([str(tmp_path), "--change", "c"])

    assert rc == 1
    assert "ScenB" in capsys.readouterr().out


def test_all_scenarios_preserved__passes(tmp_path, capsys):
    _baseline(tmp_path, "alpha", _baseline_body("Foo", "ScenA", "ScenB"))
    _delta(tmp_path, "c", "alpha", _delta_body("Foo", "ScenA", "ScenB"))

    rc = cmc.main([str(tmp_path), "--change", "c"])

    assert rc == 0
    assert "PASS" in capsys.readouterr().out


def test_allowlisted_drop__passes(tmp_path):
    _baseline(tmp_path, "alpha", _baseline_body("Foo", "ScenA", "ScenB"))
    _delta(tmp_path, "c", "alpha", _delta_body("Foo", "ScenA", allow="ScenB"))

    assert cmc.main([str(tmp_path), "--change", "c"]) == 0


def test_modified_capability_without_baseline__notes_and_passes(tmp_path, capsys):
    _delta(tmp_path, "c", "gamma", _delta_body("Baz", "ScenZ"))

    rc = cmc.main([str(tmp_path), "--change", "c"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "no baseline spec yet" in out


def test_modified_requirement_absent_from_baseline__notes_and_passes(tmp_path, capsys):
    _baseline(tmp_path, "alpha", _baseline_body("Other", "ScenA"))
    _delta(tmp_path, "c", "alpha", _delta_body("Foo", "ScenA"))

    rc = cmc.main([str(tmp_path), "--change", "c"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "no matching baseline" in out


def test_non_canonical_modified_heading__still_catches_drop(tmp_path, capsys):
    _baseline(tmp_path, "alpha", _baseline_body("Foo", "ScenA", "ScenB"))
    body = _delta_body("Foo", "ScenA").replace("## MODIFIED Requirements", "## Modified Requirements")
    _delta(tmp_path, "c", "alpha", body)

    rc = cmc.main([str(tmp_path), "--change", "c"])

    out = capsys.readouterr().out
    assert rc == 1
    assert "non-canonical MODIFIED heading" in out


# --- robustness --------------------------------------------------------------


def test_unreadable_spec__errors_with_exit_2(tmp_path, capsys):
    # baseline present so the delta is read; the delta spec.md is a directory
    _baseline(tmp_path, "alpha", _baseline_body("Foo", "ScenA"))
    (tmp_path / "changes" / "c" / "specs" / "alpha" / "spec.md").mkdir(parents=True)

    rc = cmc.main([str(tmp_path), "--change", "c"])

    assert rc == 2
    assert "ERROR" in capsys.readouterr().out


def test_unclosed_fence_in_baseline__errors_with_exit_2(tmp_path, capsys):
    baseline = _baseline_body("Foo", "ScenA") + "\nUnterminated:\n\n```python\nx = 1\n"
    _baseline(tmp_path, "alpha", baseline)
    _delta(tmp_path, "c", "alpha", _delta_body("Foo", "ScenA"))

    rc = cmc.main([str(tmp_path), "--change", "c"])

    assert rc == 2
    assert "unclosed code fence" in capsys.readouterr().out


def test_fenced_scenario_example__not_counted(tmp_path):
    baseline = _baseline_body("Foo", "ScenReal") + "\nExample:\n\n````markdown\n```\n#### Scenario: Fake\n```\n````\n"
    _baseline(tmp_path, "alpha", baseline)
    _delta(tmp_path, "c", "alpha", _delta_body("Foo", "ScenReal"))

    assert cmc.main([str(tmp_path), "--change", "c"]) == 0


def test_requirement_name_whitespace__matched_and_drop_caught(tmp_path, capsys):
    _baseline(tmp_path, "alpha", _baseline_body("Foo Bar", "ScenA", "ScenB"))
    body = _delta_body("Foo Bar", "ScenA").replace("Foo Bar", "Foo  Bar")
    _delta(tmp_path, "c", "alpha", body)

    rc = cmc.main([str(tmp_path), "--change", "c"])

    out = capsys.readouterr().out
    assert rc == 1
    assert "by normalization" in out


def test_scenario_case_variants__drop_caught(tmp_path, capsys):
    _baseline(tmp_path, "alpha", _baseline_body("Foo", "Locked Account", "locked account"))
    _delta(tmp_path, "c", "alpha", _delta_body("Foo", "Locked Account"))

    rc = cmc.main([str(tmp_path), "--change", "c"])

    assert rc == 1
    assert "locked account" in capsys.readouterr().out


def test_drop_and_unreadable__exit_2_but_failure_reported(tmp_path, capsys):
    _baseline(tmp_path, "alpha", _baseline_body("Foo", "ScenA", "ScenB"))
    _delta(tmp_path, "c", "alpha", _delta_body("Foo", "ScenA"))
    (tmp_path / "changes" / "c" / "specs" / "bad" / "spec.md").mkdir(parents=True)

    rc = cmc.main([str(tmp_path), "--change", "c"])

    out = capsys.readouterr().out
    assert rc == 2
    assert "FAIL" in out
    assert "ALSO found" in out


def test_nested_depth_spec__noted_and_passes(tmp_path, capsys):
    _write(tmp_path / "changes" / "c" / "specs" / "parent" / "child" / "spec.md", _delta_body("Whatever", "S"))

    rc = cmc.main([str(tmp_path), "--change", "c"])

    out = capsys.readouterr().out
    assert rc == 0
    assert "below the expected" in out


# --- CLI ---------------------------------------------------------------------


def test_no_active_changes__passes(tmp_path, capsys):
    rc = cmc.main([str(tmp_path)])

    assert rc == 0
    assert "nothing to check" in capsys.readouterr().out


def test_missing_change_value__exit_2(tmp_path, capsys):
    rc = cmc.main([str(tmp_path), "--change"])

    assert rc == 2
    assert "requires a value" in capsys.readouterr().err


def test_nonexistent_change__exit_2(tmp_path, capsys):
    rc = cmc.main([str(tmp_path), "--change", "nope"])

    assert rc == 2
    assert "not found" in capsys.readouterr().err


def test_specs_root_is_file__exit_2(tmp_path, capsys):
    target = tmp_path / "afile.md"
    target.write_text("x", encoding="utf-8")

    rc = cmc.main([str(target)])

    assert rc == 2
    assert "not a directory" in capsys.readouterr().err


# --- parser units ------------------------------------------------------------


def test_parse_ignores_fenced_scenario_headings():
    text = _baseline_body("Foo", "ScenReal") + "\n```\n#### Scenario: Fake\n```\n"

    parsed = cmc.parse_requirements(text, modified_only=False)

    scenarios = parsed.requirements[cmc.normalize("Foo")].scenarios
    assert "ScenReal" in scenarios
    assert "Fake" not in scenarios


def test_parse_flags_unclosed_fence():
    text = _baseline_body("Foo", "ScenA") + "\n```python\nunclosed\n"

    assert cmc.parse_requirements(text, modified_only=False).unclosed_fence is True


if __name__ == "__main__":
    _here = str(Path(__file__).resolve().parent)
    raise SystemExit(
        pytest.main([str(Path(__file__).resolve()), "-v", "-p", "no:cacheprovider", "--rootdir", _here, "--confcutdir", _here])
    )
