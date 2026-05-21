#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "pyyaml",
#   "pytest>=8.0.0",
# ]
# ///
"""Regression tests for sdd-derive's validate.py.

Behavior-level: exercise the public check functions against fixture specs and
observation YAMLs in a tmp dir, asserting the recorded failures / parse results
/ coverage classification. `main()` reads sys.argv, so the lower-level
functions (and run_single) are tested directly rather than the CLI shell.

Run: uv run tests/sdd-derive/test_validate.py
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

_MODULE_PATH = Path(__file__).resolve().parents[2] / "skills" / "sdd-derive" / "references" / "validate.py"
_spec = importlib.util.spec_from_file_location("sdd_derive_validate", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None
validate = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = validate
_spec.loader.exec_module(validate)


# --- fixtures / helpers ------------------------------------------------------

GEN_NOTE = "> Generated from code analysis on 2026-05-21, as-of commit abc1234"

WELL_FORMED_BASELINE = f"""# Foo Specification

{GEN_NOTE}

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


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _spec_file(tmp_path: Path, text: str, capability: str = "foo") -> Path:
    return _write(tmp_path / capability / "spec.md", text)


def _yaml_file(tmp_path: Path, text: str, capability: str = "foo") -> Path:
    return _write(tmp_path / f"{capability}.yaml", text)


# --- check_format ------------------------------------------------------------


def test_well_formed_baseline_passes(tmp_path):
    result = validate.check_format(_spec_file(tmp_path, WELL_FORMED_BASELINE))

    assert result.passed
    assert result.requirement_count == 1
    assert result.scenario_count == 1


def test_missing_generation_note_fails(tmp_path):
    text = WELL_FORMED_BASELINE.replace(GEN_NOTE + "\n\n", "")

    result = validate.check_format(_spec_file(tmp_path, text))

    assert not result.passed
    assert any("generation note" in f for f in result.failures)


def test_baseline_missing_purpose_fails(tmp_path):
    text = WELL_FORMED_BASELINE.replace("## Purpose\n\nHandles foo.\n\n", "")

    result = validate.check_format(_spec_file(tmp_path, text))

    assert any("Purpose" in f for f in result.failures)


def test_noncanonical_requirement_heading_fails(tmp_path):
    text = WELL_FORMED_BASELINE.replace("### Requirement: DoesFoo", "### R1: DoesFoo")

    result = validate.check_format(_spec_file(tmp_path, text))

    assert any("non-canonical" in f for f in result.failures)


def test_scenario_without_bold_when_fails(tmp_path):
    text = WELL_FORMED_BASELINE.replace("- **WHEN** an action", "- WHEN an action")

    result = validate.check_format(_spec_file(tmp_path, text))

    assert any("WHEN" in f for f in result.failures)


def test_delta_marker_in_baseline_fails(tmp_path):
    text = WELL_FORMED_BASELINE.replace("## Requirements", "## MODIFIED Requirements\n\n## Requirements")

    result = validate.check_format(_spec_file(tmp_path, text))

    assert any("delta markers" in f for f in result.failures)


def test_missing_rfc2119_fails(tmp_path):
    text = WELL_FORMED_BASELINE.replace("The system SHALL foo.", "The system foos.")

    result = validate.check_format(_spec_file(tmp_path, text))

    assert any("RFC 2119" in f for f in result.failures)


def test_stubbed_uncertainties_fails(tmp_path):
    text = WELL_FORMED_BASELINE + "\n## Uncertainties\n\n- None identified\n"

    result = validate.check_format(_spec_file(tmp_path, text))

    assert any("Uncertainties" in f for f in result.failures)


def test_nonempty_uncertainties_passes(tmp_path):
    text = WELL_FORMED_BASELINE + "\n## Uncertainties\n\n- **Edge case**: unresolved\n"

    result = validate.check_format(_spec_file(tmp_path, text))

    assert result.passed
    assert result.uncertainty_count == 1


def test_delta_output_type_allows_markers_and_no_purpose(tmp_path):
    text = f"""# Delta for Foo

{GEN_NOTE}

## MODIFIED Requirements

### Requirement: DoesFoo

The system SHALL foo better.

#### Scenario: HappyPath

- **GIVEN** a
- **WHEN** b
- **THEN** c
"""

    result = validate.check_format(_spec_file(tmp_path, text), output_type="delta")

    assert result.passed


# --- check_yaml --------------------------------------------------------------


def test_valid_yaml_parses(tmp_path):
    text = 'observations:\n  - id: obs1\nsurface_inventory:\n  - name: "GET /health"\n    kind: http_route\n'

    result = validate.check_yaml(_yaml_file(tmp_path, text))

    assert result.parsed
    assert result.observation_count == 1
    assert result.surface_count == 1


def test_invalid_yaml_reports_error(tmp_path):
    result = validate.check_yaml(_yaml_file(tmp_path, "key: [unclosed\n"))

    assert not result.parsed
    assert result.error


def test_non_mapping_yaml_rejected(tmp_path):
    result = validate.check_yaml(_yaml_file(tmp_path, "- a\n- b\n"))

    assert not result.parsed
    assert "not a mapping" in (result.error or "")


# --- check_coverage ----------------------------------------------------------

_COVERAGE_SPEC = """# Cap

## Purpose

Documents the user_created event.

## Requirements

### Requirement: R

The system SHALL serve.

#### Scenario: S

- **GIVEN** x
- **WHEN** GET /health is requested
- **THEN** ok
"""


def test_public_surface_absent_is_gap(tmp_path):
    spec = _spec_file(tmp_path, _COVERAGE_SPEC, "cap")
    yml = _yaml_file(tmp_path, 'surface_inventory:\n  - name: "POST /users"\n    kind: http_route\n', "cap")

    result = validate.check_coverage(yml, spec)

    assert any(g["name"] == "POST /users" for g in result.gaps)


def test_internal_knob_absent_is_acknowledged_not_gap(tmp_path):
    spec = _spec_file(tmp_path, _COVERAGE_SPEC, "cap")
    yml = _yaml_file(tmp_path, "surface_inventory:\n  - name: DEBUG_MODE\n    kind: env_var\n", "cap")

    result = validate.check_coverage(yml, spec)

    assert not result.gaps
    assert any(a["name"] == "DEBUG_MODE" for a in result.acknowledged)


def test_surface_in_scenario_is_covered(tmp_path):
    spec = _spec_file(tmp_path, _COVERAGE_SPEC, "cap")
    yml = _yaml_file(tmp_path, 'surface_inventory:\n  - name: "GET /health"\n    kind: http_route\n', "cap")

    result = validate.check_coverage(yml, spec)

    assert not result.gaps
    assert not any(a["name"] == "GET /health" for a in result.acknowledged)


def test_surface_mentioned_outside_scenario_is_acknowledged(tmp_path):
    spec = _spec_file(tmp_path, _COVERAGE_SPEC, "cap")
    yml = _yaml_file(tmp_path, "surface_inventory:\n  - name: user_created\n    kind: published_event\n", "cap")

    result = validate.check_coverage(yml, spec)

    assert not result.gaps
    assert any(a["name"] == "user_created" for a in result.acknowledged)


def test_substring_surface_match_is_a_gap(tmp_path):
    # "ping" is a substring of "shipping" in the spec body, but is not a real endpoint.
    spec_text = _COVERAGE_SPEC.replace("Documents the user_created event.", "Handles shipping.")
    spec = _spec_file(tmp_path, spec_text, "cap")
    yml = _yaml_file(tmp_path, "surface_inventory:\n  - name: ping\n    kind: http_route\n", "cap")

    result = validate.check_coverage(yml, spec)

    assert any(g["name"] == "ping" for g in result.gaps)


def test_case_variant_surface_is_a_gap(tmp_path):
    # "GetUser" vs lowercase "getuser" — surface case is significant, so this is a gap.
    spec_text = _COVERAGE_SPEC.replace("Documents the user_created event.", "Handles getuser flows.")
    spec = _spec_file(tmp_path, spec_text, "cap")
    yml = _yaml_file(tmp_path, "surface_inventory:\n  - name: GetUser\n    kind: exported_symbol\n", "cap")

    result = validate.check_coverage(yml, spec)

    assert any(g["name"] == "GetUser" for g in result.gaps)


def test_subtoken_surface_is_a_gap(tmp_path):
    # "User" must not match as a sub-token of "UserService".
    spec_text = _COVERAGE_SPEC.replace("Documents the user_created event.", "Calls UserService here.")
    spec = _spec_file(tmp_path, spec_text, "cap")
    yml = _yaml_file(tmp_path, "surface_inventory:\n  - name: User\n    kind: exported_symbol\n", "cap")

    result = validate.check_coverage(yml, spec)

    assert any(g["name"] == "User" for g in result.gaps)


def test_route_with_leading_slash_is_matched(tmp_path):
    # leading-slash route must still match (a bare word boundary would fail here).
    spec_text = _COVERAGE_SPEC.replace("GET /health", "/health")
    spec = _spec_file(tmp_path, spec_text, "cap")
    yml = _yaml_file(tmp_path, 'surface_inventory:\n  - name: "/health"\n    kind: http_route\n', "cap")

    result = validate.check_coverage(yml, spec)

    assert not any(g["name"] == "/health" for g in result.gaps)


# --- run_single (integration) ------------------------------------------------


def test_run_single_well_formed_returns_0(tmp_path, capsys):
    spec = _spec_file(tmp_path, WELL_FORMED_BASELINE)
    yml = _yaml_file(tmp_path, "observations:\n  - id: o1\n")

    rc = validate.run_single(yml, spec)

    assert rc == 0
    assert "PASS" in capsys.readouterr().out


def test_run_single_format_failure_returns_1(tmp_path):
    spec = _spec_file(tmp_path, WELL_FORMED_BASELINE.replace("## Purpose\n\nHandles foo.\n\n", ""))
    yml = _yaml_file(tmp_path, "observations:\n  - id: o1\n")

    assert validate.run_single(yml, spec) == 1


def test_run_single_missing_file_returns_2(tmp_path):
    spec = _spec_file(tmp_path, WELL_FORMED_BASELINE)

    assert validate.run_single(tmp_path / "missing.yaml", spec) == 2


if __name__ == "__main__":
    _here = str(Path(__file__).resolve().parent)
    raise SystemExit(
        pytest.main([str(Path(__file__).resolve()), "-v", "-p", "no:cacheprovider", "--rootdir", _here, "--confcutdir", _here])
    )
