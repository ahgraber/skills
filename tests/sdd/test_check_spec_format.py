#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8.0.0",
# ]
# ///
"""Regression tests for the shared spec format check.

Behavior-level: feed spec markdown through check_spec_format and assert what it
records. The regressions that motivated the script — a delta marker fused to a
requirement heading, a requirement promoted to H2, a baseline with no
`## Requirements` container — each get a named test.

Run: uv run tests/sdd/test_check_spec_format.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "skills" / "sdd" / "scripts" / "check_spec_format.py"
_spec = importlib.util.spec_from_file_location("sdd_check_spec_format", _MODULE_PATH)
assert _spec is not None
assert _spec.loader is not None
csf = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = csf
_spec.loader.exec_module(csf)


BASELINE = """# Foo Specification

## Purpose

Handles foo.

## Requirements

### Requirement: DoesFoo

The system SHALL foo.

#### Scenario: HappyPath

- **GIVEN** a precondition
- **WHEN** an action
- **THEN** an outcome
"""

DELTA = """# Delta for Foo

## ADDED Requirements

### Requirement: DoesFoo

The system SHALL foo.

Serves: foo-story

#### Scenario: HappyPath

- **GIVEN** a precondition
- **WHEN** an action
- **THEN** an outcome
"""

PATH = Path("specs/foo/spec.md")


def _check(text: str, output_type: str = "auto"):
    return csf.check_spec_format(text, PATH, output_type)


def _messages(text: str, output_type: str = "auto") -> str:
    return "\n".join(_check(text, output_type).failures)


# --- happy paths -------------------------------------------------------------


def test_well_formed_baseline_passes():
    result = _check(BASELINE)

    assert result.passed, result.failures
    assert result.output_type == "baseline"
    assert result.requirement_count == 1
    assert result.scenario_count == 1


def test_well_formed_delta_passes():
    result = _check(DELTA)

    assert result.passed, result.failures
    assert result.output_type == "delta"


def test_removed_only_delta_needs_no_rfc2119():
    text = """# Delta for Foo

## REMOVED Requirements

### Requirement: DoesFoo

Removed because: the capability moved to bar.
"""

    assert _check(text).passed


# --- the regressions this script exists for ----------------------------------


def test_marker_fused_to_requirement_heading_fails():
    text = DELTA.replace("## ADDED Requirements\n\n### Requirement: DoesFoo", "## ADDED Requirement: DoesFoo")

    messages = _messages(text)

    assert "fused" in messages
    assert "## ADDED Requirements" in messages


def test_marker_fused_at_h3_fails():
    text = DELTA.replace("### Requirement: DoesFoo", "### ADDED Requirement: DoesFoo")

    assert "fused" in _messages(text)


def test_requirement_promoted_to_h2_fails():
    text = BASELINE.replace("### Requirement: DoesFoo", "## Requirement: DoesFoo")

    messages = _messages(text)

    assert "requirement heading at H2" in messages


def test_scenario_promoted_to_h3_fails():
    text = BASELINE.replace("#### Scenario: HappyPath", "### Scenario: HappyPath")

    assert "scenario heading at H3" in _messages(text)


def test_baseline_without_requirements_container_fails():
    text = BASELINE.replace("## Requirements\n\n", "")

    assert "'## Requirements'" in _messages(text)


def test_requirement_above_requirements_container_fails():
    text = BASELINE.replace(
        "## Requirements\n",
        "### Requirement: Stray\n\nThe system SHALL stray.\n\n## Requirements\n",
    )

    assert "appears before the '## Requirements' heading" in _messages(text)


def test_delta_without_section_heading_fails():
    text = DELTA.replace("## ADDED Requirements\n\n", "")

    assert "no delta section heading found" in _messages(text)


# --- remaining baseline rules ------------------------------------------------


def test_baseline_missing_purpose_fails():
    text = BASELINE.replace("## Purpose\n\nHandles foo.\n\n", "")

    assert "'## Purpose'" in _messages(text)


def test_baseline_missing_title_fails():
    text = BASELINE.replace("# Foo Specification\n\n", "")

    assert "H1 title" in _messages(text)


def test_baseline_without_requirements_fails():
    text = "# Foo Specification\n\n## Purpose\n\nFoo.\n\n## Requirements\n\nThe system SHALL foo.\n"

    assert "no requirement headings found" in _messages(text)


def test_delta_marker_in_baseline_fails():
    text = BASELINE.replace("## Requirements", "## MODIFIED Requirements\n\n## Requirements")

    assert "delta marker" in _messages(text, output_type="baseline")


def test_missing_rfc2119_fails():
    text = BASELINE.replace("The system SHALL foo.", "The system foos.")

    assert "RFC 2119" in _messages(text)


# --- remaining delta rules ---------------------------------------------------


def test_purpose_in_delta_fails():
    text = DELTA.replace("## ADDED Requirements", "## Purpose\n\nFoo.\n\n## ADDED Requirements")

    assert "not allowed in a delta spec" in _messages(text)


def test_technical_notes_in_delta_fails():
    text = DELTA + "\n## Technical Notes\n\n- **Implementation**: foo.py\n"

    assert "not allowed in a delta spec" in _messages(text)


def test_requirement_above_delta_section_fails():
    text = DELTA.replace(
        "## ADDED Requirements\n",
        "### Requirement: Stray\n\nThe system SHALL stray.\n\n## ADDED Requirements\n",
    )

    assert "appears before any delta section heading" in _messages(text)


# --- scenarios ---------------------------------------------------------------


@pytest.mark.parametrize("label", ["GIVEN", "WHEN", "THEN"])
def test_scenario_without_bold_label_fails(label):
    text = BASELINE.replace(f"**{label}**", label)

    assert f"**{label}**" in _messages(text)


def test_scenario_before_any_requirement_fails():
    text = BASELINE.replace(
        "### Requirement: DoesFoo",
        "#### Scenario: Orphan\n\n- **GIVEN** a\n- **WHEN** b\n- **THEN** c\n\n### Requirement: DoesFoo",
    )

    assert "appears before any requirement" in _messages(text)


# --- parsing -----------------------------------------------------------------


def test_headings_inside_fenced_block_are_ignored():
    text = BASELINE + "\n```markdown\n## Requirement: NotReal\n### Scenario: NotReal\n```\n"

    assert _check(text).passed


def test_detect_output_type_reads_markers_not_path():
    assert csf.detect_output_type(DELTA, PATH) == "delta"
    assert csf.detect_output_type(BASELINE, PATH) == "baseline"


def test_malformed_delta_is_still_detected_as_delta():
    text = DELTA.replace("## ADDED Requirements\n\n### Requirement: DoesFoo", "## ADDED Requirement: DoesFoo")

    assert csf.detect_output_type(text, PATH) == "delta"


def test_forced_output_type_overrides_detection():
    result = _check(DELTA, output_type="baseline")

    assert result.output_type == "baseline"
    assert "delta marker" in "\n".join(result.failures)


# --- file and CLI surface ----------------------------------------------------


def test_missing_file_is_a_failure(tmp_path):
    result = csf.check_spec_file(tmp_path / "nope" / "spec.md")

    assert not result.passed
    assert "not found" in result.failures[0]


def test_collect_specs_expands_directories(tmp_path):
    (tmp_path / "foo").mkdir()
    (tmp_path / "foo" / "spec.md").write_text(BASELINE, encoding="utf-8")
    (tmp_path / "foo" / "design.md").write_text("not a spec", encoding="utf-8")

    found = csf.collect_specs([tmp_path])

    assert found == [tmp_path / "foo" / "spec.md"]


def test_cli_returns_nonzero_on_failure(tmp_path, monkeypatch, capsys):
    spec = tmp_path / "foo" / "spec.md"
    spec.parent.mkdir()
    spec.write_text(BASELINE.replace("### Requirement: DoesFoo", "## Requirement: DoesFoo"), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_spec_format.py", str(spec)])

    assert csf.main() == 1
    assert "requirement heading at H2" in capsys.readouterr().out


def test_cli_returns_zero_on_pass(tmp_path, monkeypatch, capsys):
    spec = tmp_path / "foo" / "spec.md"
    spec.parent.mkdir()
    spec.write_text(BASELINE, encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["check_spec_format.py", "--type", "baseline", str(spec)])

    assert csf.main() == 0
    assert "PASS" in capsys.readouterr().out


if __name__ == "__main__":
    here = str(Path(__file__).parent)
    raise SystemExit(pytest.main([__file__, "-q", "--rootdir", here, "--confcutdir", here]))
