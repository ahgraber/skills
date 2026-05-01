# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Deterministic validator for sdd-derive.

Runs three checks against observation YAMLs and spec markdown files:

1. **YAML parse check** — every observation YAML must yaml.safe_load cleanly.
2. **Format check** — every spec.md matches the canonical baseline/delta shape from
   references/sdd-spec-formats.md (generation note, ## Purpose for baseline,
   ### Requirement: <Name> headings, #### Scenario: blocks with bold GIVEN/WHEN/THEN,
   no delta markers in baseline, ## Uncertainties only-when-non-empty).
3. **Surface coverage diff** — kind-aware: public-consumer surfaces absent from spec
   are gaps; internal-knob surfaces (env_var, config_key, cli_flag) absent default to
   acknowledged-without-scenario per references/validate.md.

Two modes:

- **Single mode** — used by the lifter against its own output before returning.
  Catches format failures at write time (no orchestrator round-trip).
  Format check + YAML parse check + per-capability surface coverage.

      uv run --quiet validate.py --single <observations.yaml> <spec.md>

- **Aggregate mode** — used by the orchestrator at Phase 5 across the whole run.
  All capabilities at once; cross-capability totals; final report.

      uv run --quiet validate.py <observations_dir> <specs_dir>

Exit code is non-zero if any spec fails format or any YAML fails to parse.
Surface gaps and uncertainties are informational; they do not fail the run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re
import sys
import yaml

# --- Surface kind classification per references/validate.md -----------------

PUBLIC_CONSUMER_KINDS = frozenset(
    {"http_route", "grpc_method", "cli_command", "published_event", "exported_symbol"}
)
INTERNAL_KNOB_KINDS = frozenset({"env_var", "config_key", "cli_flag"})

# --- Spec format regexes ----------------------------------------------------

GENERATION_NOTE = re.compile(
    r"^>\s+Generated from code analysis on \d{4}-\d{2}-\d{2}, as-of commit [0-9a-f]{7,40}\b",
    re.MULTILINE,
)
PURPOSE_HEADING = re.compile(r"^##\s+Purpose\s*$", re.MULTILINE)
REQUIREMENTS_HEADING = re.compile(r"^##\s+Requirements\s*$", re.MULTILINE)
REQUIREMENT_HEADING = re.compile(r"^###\s+Requirement:\s+\S", re.MULTILINE)
SCENARIO_HEADING = re.compile(r"^####\s+Scenario:\s+\S", re.MULTILINE)
GIVEN_BOLD = re.compile(r"\*\*GIVEN\*\*")
WHEN_BOLD = re.compile(r"\*\*WHEN\*\*")
THEN_BOLD = re.compile(r"\*\*THEN\*\*")
DELTA_MARKER = re.compile(
    r"^##\s+(ADDED|MODIFIED|REMOVED|RENAMED)\s+(Requirements|Capabilities)\s*$",
    re.MULTILINE,
)
UNCERTAINTIES_HEADING = re.compile(r"^##\s+Uncertainties\s*$", re.MULTILINE)
RFC_2119 = re.compile(r"\b(SHALL|MUST|SHOULD|MAY)\b")

# Heuristic patterns indicating a non-canonical requirement heading shape
NONCANONICAL_REQ = re.compile(
    r"^###\s+(R\d+|REQ-\d+|Req\s*#?\d+|Requirement\s*\d+)[:\s]", re.MULTILINE
)


# --- Result types -----------------------------------------------------------


@dataclass
class FormatResult:
    capability: str
    spec_path: Path
    failures: list[str] = field(default_factory=list)
    requirement_count: int = 0
    scenario_count: int = 0
    uncertainty_present: bool = False
    uncertainty_count: int = 0

    @property
    def passed(self) -> bool:
        """True when the spec produced no format failures."""
        return not self.failures


@dataclass
class YamlResult:
    capability: str
    yaml_path: Path
    parsed: bool
    error: str | None = None
    observation_count: int = 0
    surface_count: int = 0


@dataclass
class CoverageResult:
    capability: str
    gaps: list[dict] = field(default_factory=list)
    acknowledged: list[dict] = field(default_factory=list)
    surfaces_total: int = 0


# --- Format check -----------------------------------------------------------


def check_format(spec_path: Path, output_type: str = "baseline") -> FormatResult:
    """Run regex-based format checks against a spec file.

    output_type: "baseline" or "delta"
    """
    cap = spec_path.parent.name
    result = FormatResult(capability=cap, spec_path=spec_path)
    text = spec_path.read_text()

    # 1. Generation note
    if not GENERATION_NOTE.search(text):
        result.failures.append(
            "missing generation note ('> Generated from code analysis on YYYY-MM-DD, as-of commit <sha>')"
        )

    # 2. Purpose section (baseline only)
    if output_type == "baseline" and not PURPOSE_HEADING.search(text):
        result.failures.append("missing '## Purpose' section (required in baseline)")

    # 3. Requirement headings — canonical shape
    req_count = len(REQUIREMENT_HEADING.findall(text))
    noncanonical_reqs = NONCANONICAL_REQ.findall(text)
    if noncanonical_reqs:
        result.failures.append(
            f"non-canonical requirement headings: found {len(noncanonical_reqs)} entries "
            f"matching '### R<n>:' / '### REQ-<n>:' / '### Req #<n>:'; expected '### Requirement: <Name>'"
        )
    if req_count == 0 and not noncanonical_reqs:
        result.failures.append("no requirement headings found")
    result.requirement_count = req_count

    # 4. Scenario headings + bold GIVEN/WHEN/THEN
    scen_count = len(SCENARIO_HEADING.findall(text))
    given = len(GIVEN_BOLD.findall(text))
    when = len(WHEN_BOLD.findall(text))
    then = len(THEN_BOLD.findall(text))
    if scen_count > 0:
        # Each scenario should have at least one GIVEN, one WHEN, one THEN.
        # Allow for compound scenarios (multiple WHEN/THEN clauses).
        if given < scen_count:
            result.failures.append(
                f"only {given} bold **GIVEN** markers for {scen_count} scenarios"
            )
        if when < scen_count:
            result.failures.append(
                f"only {when} bold **WHEN** markers for {scen_count} scenarios"
            )
        if then < scen_count:
            result.failures.append(
                f"only {then} bold **THEN** markers for {scen_count} scenarios"
            )
    result.scenario_count = scen_count

    # 5. No delta markers in baseline
    if output_type == "baseline":
        delta_hits = DELTA_MARKER.findall(text)
        if delta_hits:
            result.failures.append(
                f"baseline spec contains delta markers: {[m[0] + ' ' + m[1] for m in delta_hits]}"
            )

    # 6. RFC 2119 keyword usage
    if not RFC_2119.search(text):
        result.failures.append(
            "no RFC 2119 keywords (SHALL/MUST/SHOULD/MAY) found"
        )

    # 7. Uncertainties section: present iff non-empty
    if UNCERTAINTIES_HEADING.search(text):
        # Count uncertainty entries (top-level bullet items under the heading)
        m = UNCERTAINTIES_HEADING.search(text)
        body = text[m.end() :] if m else ""
        # Stop at next H2
        next_h2 = re.search(r"^##\s+\S", body, re.MULTILINE)
        if next_h2:
            body = body[: next_h2.start()]
        # Top-level bullets start with "- **"
        uncertainty_entries = re.findall(
            r"^\s*-\s+\*\*", body, re.MULTILINE
        )
        result.uncertainty_present = True
        result.uncertainty_count = len(uncertainty_entries)
        # Detect "None identified" / "No uncertainties" prose stub
        stub_words = re.search(
            r"\b(none identified|no uncertainties|nothing flagged|n/a)\b",
            body,
            re.IGNORECASE,
        )
        if result.uncertainty_count == 0 or stub_words:
            result.failures.append(
                "'## Uncertainties' section is present but empty or stubbed; OMIT entirely when empty"
            )

    return result


# --- YAML parse check -------------------------------------------------------


def check_yaml(yaml_path: Path) -> YamlResult:
    """Parse an observation YAML and report observation and surface counts.

    Returns a YamlResult with parsed=False and an error string when YAML
    parsing fails or the top-level value is not a mapping.
    """
    cap = yaml_path.stem
    try:
        data = yaml.safe_load(yaml_path.read_text())
    except yaml.YAMLError as e:
        return YamlResult(
            capability=cap, yaml_path=yaml_path, parsed=False, error=str(e)
        )

    if not isinstance(data, dict):
        return YamlResult(
            capability=cap,
            yaml_path=yaml_path,
            parsed=False,
            error="top-level YAML is not a mapping",
        )

    obs = data.get("observations") or []
    inv = data.get("surface_inventory") or []
    return YamlResult(
        capability=cap,
        yaml_path=yaml_path,
        parsed=True,
        observation_count=len(obs) if isinstance(obs, list) else 0,
        surface_count=len(inv) if isinstance(inv, list) else 0,
    )


# --- Surface coverage diff --------------------------------------------------


def check_coverage(yaml_path: Path, spec_path: Path) -> CoverageResult:
    """Diff the surface inventory against the spec, kind-aware.

    Public-consumer surfaces absent from the spec are gaps; internal-knob
    surfaces (env_var, config_key, cli_flag) absent default to
    acknowledged-without-scenario per references/validate.md. Surfaces
    mentioned in the spec but not inside any `#### Scenario:` block are
    also acknowledged.
    """
    cap = yaml_path.stem
    result = CoverageResult(capability=cap)
    try:
        data = yaml.safe_load(yaml_path.read_text())
    except yaml.YAMLError:
        return result  # YAML parse failure already recorded

    if not isinstance(data, dict):
        return result

    inv = data.get("surface_inventory") or []
    if not isinstance(inv, list):
        return result

    spec_text = spec_path.read_text() if spec_path.exists() else ""

    # Collect scenario blocks for "mentioned but no scenario" detection
    scen_blocks = re.findall(
        r"####\s*Scenario:.*?(?=####\s*Scenario:|^###\s|\Z)",
        spec_text,
        re.DOTALL | re.MULTILINE,
    )
    scen_text = "\n".join(scen_blocks)

    for item in inv:
        if not isinstance(item, dict):
            continue
        name = item.get("name", "")
        kind = item.get("kind", "unknown")
        if not name:
            continue
        result.surfaces_total += 1
        is_internal_knob = kind in INTERNAL_KNOB_KINDS
        is_public = kind in PUBLIC_CONSUMER_KINDS

        in_spec = name in spec_text
        in_scenario = name in scen_text if scen_blocks else False

        entry = {"kind": kind, "name": name}

        if not in_spec:
            # Internal knobs default to acknowledged-without-scenario when absent
            if is_internal_knob:
                result.acknowledged.append(entry | {"reason": "internal-knob; lift discipline excludes"})
            elif is_public:
                result.gaps.append(entry | {"reason": "public-consumer surface absent from spec"})
            else:
                # Unknown kind — conservatively flag as gap so user reviews
                result.gaps.append(entry | {"reason": f"surface kind '{kind}' absent; unrecognized — review"})
        elif in_spec and not in_scenario:
            # Mentioned but no scenario covers it
            result.acknowledged.append(entry | {"reason": "mentioned in spec; no scenario covers it"})

    return result


# --- Driver -----------------------------------------------------------------


def run_single(yaml_path: Path, spec_path: Path) -> int:
    """Validate one capability — used by the lifter before returning.

    Output is tight and actionable: lists exact failures or prints PASS.
    Exit code is non-zero on any format or YAML failure.
    """
    if not yaml_path.exists():
        print(f"FAIL  observations YAML not found: {yaml_path}", file=sys.stderr)
        return 2
    if not spec_path.exists():
        print(f"FAIL  spec not found: {spec_path}", file=sys.stderr)
        return 2

    failures: list[str] = []

    # YAML parse
    yr = check_yaml(yaml_path)
    if not yr.parsed:
        failures.append(f"YAML parse error in {yaml_path.name}: {yr.error}")

    # Format
    fr = check_format(spec_path, output_type="baseline")
    if not fr.passed:
        failures.extend(fr.failures)

    # Coverage (per-cap, informational only)
    cov = check_coverage(yaml_path, spec_path)

    cap = yaml_path.stem
    if failures:
        print(f"FAIL  {cap}")
        for msg in failures:
            print(f"  - {msg}")
        if cov.gaps:
            print(f"  surface gaps (informational): {len(cov.gaps)}")
        return 1

    print(
        f"PASS  {cap}  reqs={fr.requirement_count} scenarios={fr.scenario_count} "
        f"uncertainties={fr.uncertainty_count} surface_gaps={len(cov.gaps)} "
        f"acknowledged={len(cov.acknowledged)}"
    )
    return 0


def main() -> int:
    """Parse argv, dispatch to single or aggregate mode, return exit code."""
    args = sys.argv[1:]

    if len(args) >= 1 and args[0] == "--single":
        if len(args) != 3:
            print(
                "Usage: uv run --quiet validate.py --single <observations.yaml> <spec.md>",
                file=sys.stderr,
            )
            return 2
        return run_single(Path(args[1]), Path(args[2]))

    if len(args) != 2:
        print(
            "Usage: uv run --quiet validate.py <observations_dir> <specs_dir>\n"
            "       uv run --quiet validate.py --single <observations.yaml> <spec.md>",
            file=sys.stderr,
        )
        return 2

    obs_dir = Path(args[0])
    spec_dir = Path(args[1])

    if not obs_dir.is_dir():
        print(f"observations dir not found: {obs_dir}", file=sys.stderr)
        return 2
    if not spec_dir.is_dir():
        print(f"specs dir not found: {spec_dir}", file=sys.stderr)
        return 2

    yaml_files = sorted(obs_dir.glob("*.yaml"))
    if not yaml_files:
        print(f"no *.yaml files in {obs_dir}", file=sys.stderr)
        return 2

    yaml_results: list[YamlResult] = []
    format_results: list[FormatResult] = []
    coverage_results: list[CoverageResult] = []

    for yp in yaml_files:
        cap = yp.stem
        sp = spec_dir / cap / "spec.md"
        yaml_results.append(check_yaml(yp))
        if sp.exists():
            format_results.append(check_format(sp, output_type="baseline"))
            coverage_results.append(check_coverage(yp, sp))
        else:
            # Spec missing — record a synthetic failure
            r = FormatResult(capability=cap, spec_path=sp)
            r.failures.append(f"spec file not found at {sp}")
            format_results.append(r)

    # ------------------------------------------------------------------ report
    any_failure = False

    print("=" * 78)
    print("SDD-Derive Validate Report")
    print("=" * 78)

    # YAML
    print("\n## YAML parse check")
    yaml_failed = [r for r in yaml_results if not r.parsed]
    print(f"  {len(yaml_results) - len(yaml_failed)}/{len(yaml_results)} observation YAMLs parsed cleanly")
    for r in yaml_failed:
        any_failure = True
        print(f"  FAIL  {r.capability}: {r.error}")

    # Format
    print("\n## Format check")
    fmt_failed = [r for r in format_results if not r.passed]
    print(
        f"  {len(format_results) - len(fmt_failed)}/{len(format_results)} specs match canonical format"
    )
    for r in format_results:
        status = "PASS" if r.passed else "FAIL"
        print(
            f"  {status}  {r.capability:<42} reqs={r.requirement_count:<3} scenarios={r.scenario_count:<3} uncertainties={r.uncertainty_count}"
        )
        if not r.passed:
            any_failure = True
            for f in r.failures:
                print(f"        - {f}")

    # Coverage
    print("\n## Surface coverage diff")
    total_surfaces = sum(c.surfaces_total for c in coverage_results)
    total_gaps = sum(len(c.gaps) for c in coverage_results)
    total_acked = sum(len(c.acknowledged) for c in coverage_results)
    print(
        f"  surfaces={total_surfaces}  gaps={total_gaps}  acknowledged={total_acked}"
    )
    for c in coverage_results:
        if c.gaps:
            print(f"  {c.capability}: {len(c.gaps)} gap(s)")
            for g in c.gaps[:8]:
                print(f"    - [{g['kind']}] {g['name']} — {g['reason']}")
            if len(c.gaps) > 8:
                print(f"    ... +{len(c.gaps) - 8} more")

    # Summary
    print("\n## Summary")
    print(
        f"  YAML parse failures:  {len(yaml_failed)} of {len(yaml_results)}"
    )
    print(
        f"  Format failures:      {len(fmt_failed)} of {len(format_results)}"
    )
    print(
        f"  Surface gaps:         {total_gaps} (informational; not blocking)"
    )
    print(
        f"  Acknowledged:         {total_acked} (informational; internal knobs OK)"
    )

    # JSON output for machine consumption (last line)
    summary = {
        "yaml_total": len(yaml_results),
        "yaml_failures": len(yaml_failed),
        "format_total": len(format_results),
        "format_failures": len(fmt_failed),
        "surfaces_total": total_surfaces,
        "surface_gaps": total_gaps,
        "surfaces_acknowledged": total_acked,
        "uncertainties_total": sum(r.uncertainty_count for r in format_results),
    }
    print("\n## Machine-readable summary")
    print(json.dumps(summary))

    return 1 if any_failure else 0


if __name__ == "__main__":
    sys.exit(main())
