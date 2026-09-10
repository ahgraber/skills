#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = []
# ///
"""Structural format check for SDD `spec.md` files.

Checks the heading rules in `references/sdd-spec-formats.md` § 3 (baseline) and
§ 4 (delta): heading levels, the `## Requirements` container, delta section
headings, scenario nesting, and bold GIVEN/WHEN/THEN.

Owned by the `sdd` skill and symlinked into the scripts/ directory of
sdd-propose, sdd-derive, sdd-sync, and sdd-translate.

    uv run --quiet check_spec_format.py <path>...
    uv run --quiet check_spec_format.py --type delta <path>...

Paths may be `spec.md` files or directories (searched for `**/spec.md`).
Baseline or delta is detected per file unless `--type` forces one.
Exit code is non-zero when any file fails.

Structure only; § 1 contract shape is left to the calling skill.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys

HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE = re.compile(r"^\s*(?:```|~~~)")

DELTA_SECTION = re.compile(r"^(ADDED|MODIFIED|REMOVED)\s+Requirements$")
RENAMED_SECTION = re.compile(r"^RENAMED\s+Capabilities$")
FUSED_MARKER = re.compile(r"^(ADDED|MODIFIED|REMOVED|RENAMED)\s+(Requirement|Capability)\b:?\s*(.*)$")
REQUIREMENT = re.compile(r"^Requirement:\s*(\S.*)$")
SCENARIO = re.compile(r"^Scenario:\s*(\S.*)$")
RFC_2119 = re.compile(r"\b(SHALL|MUST|SHOULD|MAY)\b")
GWT_LABELS = {label: re.compile(rf"\*\*{label}\*\*") for label in ("GIVEN", "WHEN", "THEN")}

REQUIREMENT_LEVEL = 3
SCENARIO_LEVEL = 4


@dataclass
class Heading:
    """One markdown heading outside any fenced code block."""

    level: int
    text: str
    line: int
    body: str = ""

    @property
    def marked(self) -> str:
        """The heading as written, for quoting back in a failure message."""
        return f"{'#' * self.level} {self.text}"


@dataclass
class SpecFormatResult:
    """Outcome of checking one spec file."""

    path: Path
    output_type: str
    failures: list[str] = field(default_factory=list)
    requirement_count: int = 0
    scenario_count: int = 0

    @property
    def passed(self) -> bool:
        """True when the spec produced no format failures."""
        return not self.failures


def parse_headings(text: str) -> list[Heading]:
    """Return every heading outside fenced code blocks, each with its body text.

    Fenced blocks are skipped so a spec that quotes markdown in an example does
    not report the quoted headings as its own.
    """
    lines = text.splitlines()
    headings: list[Heading] = []
    starts: list[int] = []
    in_fence = False

    for i, line in enumerate(lines):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = HEADING.match(line)
        if m:
            headings.append(Heading(level=len(m.group(1)), text=m.group(2), line=i + 1))
            starts.append(i)

    for idx, heading in enumerate(headings):
        start = starts[idx] + 1
        end = starts[idx + 1] if idx + 1 < len(headings) else len(lines)
        heading.body = "\n".join(lines[start:end])

    return headings


def detect_output_type(text: str, path: Path | None = None) -> str:
    """Classify a spec as "delta" or "baseline" from its own content.

    Any delta marker makes it a delta, including one fused to a requirement
    heading, so a malformed delta is checked against the delta rules.
    """
    for heading in parse_headings(text):
        if DELTA_SECTION.match(heading.text) or RENAMED_SECTION.match(heading.text):
            return "delta"
        if FUSED_MARKER.match(heading.text):
            return "delta"
        if heading.level == 1 and heading.text.lower().startswith("delta"):
            return "delta"
    if path is not None and "changes" in path.parts:
        return "delta"
    return "baseline"


def _check_scenario_bodies(headings: list[Heading], failures: list[str]) -> None:
    """Require bold GIVEN/WHEN/THEN inside each scenario block."""
    for heading in headings:
        m = SCENARIO.match(heading.text)
        if not m:
            continue
        for label, pattern in GWT_LABELS.items():
            if not pattern.search(heading.body):
                failures.append(f"line {heading.line}: scenario '{m.group(1)}' has no bold **{label}** (§ 5)")


def _check_levels(headings: list[Heading], failures: list[str]) -> tuple[int, int]:
    """Require requirement headings at H3 and scenario headings at H4.

    Returns the count of correctly levelled requirements and scenarios.
    """
    requirements = 0
    scenarios = 0
    for heading in headings:
        if REQUIREMENT.match(heading.text):
            if heading.level == REQUIREMENT_LEVEL:
                requirements += 1
            else:
                failures.append(
                    f"line {heading.line}: requirement heading at H{heading.level}: '{heading.marked}' — "
                    f"requirements are '### Requirement: <Name>' exactly (§ 3)"
                )
        elif SCENARIO.match(heading.text):
            if heading.level == SCENARIO_LEVEL:
                scenarios += 1
            else:
                failures.append(
                    f"line {heading.line}: scenario heading at H{heading.level}: '{heading.marked}' — "
                    f"scenarios are '#### Scenario: <Name>' exactly (§ 5)"
                )
    return requirements, scenarios


def _check_baseline(headings: list[Heading], result: SpecFormatResult) -> None:
    """Apply the § 3 baseline rules."""
    failures = result.failures

    if not any(h.level == 1 for h in headings):
        failures.append("missing H1 title ('# <Capability> Specification') (§ 3)")
    if not any(h.level == 2 and h.text == "Purpose" for h in headings):
        failures.append("missing '## Purpose' section (§ 3)")

    requirements_line = next((h.line for h in headings if h.level == 2 and h.text == "Requirements"), None)
    if requirements_line is None:
        failures.append("missing '## Requirements' container heading — requirements nest under it (§ 3)")

    for heading in headings:
        if heading.level != 2:
            continue
        if (
            DELTA_SECTION.match(heading.text)
            or RENAMED_SECTION.match(heading.text)
            or FUSED_MARKER.match(heading.text)
        ):
            failures.append(f"line {heading.line}: delta marker '{heading.marked}' in a baseline spec (§ 3)")

    result.requirement_count, result.scenario_count = _check_levels(headings, failures)

    if requirements_line is not None:
        for heading in headings:
            if REQUIREMENT.match(heading.text) and heading.line < requirements_line:
                failures.append(
                    f"line {heading.line}: '{heading.marked}' appears before the '## Requirements' heading (§ 3)"
                )

    if not any(REQUIREMENT.match(h.text) for h in headings):
        failures.append("no requirement headings found (§ 3)")

    _check_orphan_scenarios(headings, failures)
    _check_scenario_bodies(headings, failures)

    if not RFC_2119.search("\n".join(h.body for h in headings)):
        failures.append("no RFC 2119 keywords (SHALL/MUST/SHOULD/MAY) found (§ 2)")


def _check_delta(headings: list[Heading], result: SpecFormatResult) -> None:
    """Apply the § 4 delta rules."""
    failures = result.failures

    if not any(h.level == 1 for h in headings):
        failures.append("missing H1 title ('# Delta for <Capability>') (§ 4)")

    sections = [h for h in headings if h.level == 2 and (DELTA_SECTION.match(h.text) or RENAMED_SECTION.match(h.text))]

    for heading in headings:
        m = FUSED_MARKER.match(heading.text)
        if not m:
            continue
        marker, noun, name = m.group(1), m.group(2), m.group(3) or "<Name>"
        container = "RENAMED Capabilities" if marker == "RENAMED" else f"{marker} Requirements"
        failures.append(
            f"line {heading.line}: delta marker fused to a {noun.lower()} heading: '{heading.marked}' — "
            f"'## {container}' is a section heading holding many '### {noun}: <Name>' entries, "
            f"never a per-{noun.lower()} prefix; write '## {container}' once, then '### Requirement: {name}' (§ 4)"
        )

    if not sections:
        failures.append(
            "no delta section heading found — a delta spec groups its requirements under "
            "'## ADDED Requirements', '## MODIFIED Requirements', '## REMOVED Requirements', "
            "or '## RENAMED Capabilities' (§ 4)"
        )

    for heading in headings:
        if heading.level == 2 and heading.text in ("Purpose", "Technical Notes"):
            failures.append(f"line {heading.line}: '{heading.marked}' is not allowed in a delta spec (§ 4)")

    result.requirement_count, result.scenario_count = _check_levels(headings, failures)

    if sections:
        first_section = sections[0].line
        for heading in headings:
            if REQUIREMENT.match(heading.text) and heading.line < first_section:
                failures.append(
                    f"line {heading.line}: '{heading.marked}' appears before any delta section heading (§ 4)"
                )

    _check_orphan_scenarios(headings, failures)
    _check_scenario_bodies(headings, failures)

    covered = [h for h in sections if DELTA_SECTION.match(h.text) and not h.text.startswith("REMOVED")]
    if covered and not RFC_2119.search("\n".join(h.body for h in headings)):
        failures.append("no RFC 2119 keywords (SHALL/MUST/SHOULD/MAY) found (§ 2)")


def _check_orphan_scenarios(headings: list[Heading], failures: list[str]) -> None:
    """Require every scenario to follow a requirement heading."""
    seen_requirement = False
    for heading in headings:
        if REQUIREMENT.match(heading.text):
            seen_requirement = True
            continue
        m = SCENARIO.match(heading.text)
        if m and not seen_requirement:
            failures.append(
                f"line {heading.line}: scenario '{m.group(1)}' appears before any requirement — "
                f"scenarios nest inside the requirement they sample (§ 1.5)"
            )


def check_spec_format(text: str, path: Path, output_type: str = "auto") -> SpecFormatResult:
    """Check one spec's heading structure and return the recorded failures."""
    resolved = detect_output_type(text, path) if output_type == "auto" else output_type
    result = SpecFormatResult(path=path, output_type=resolved)
    headings = parse_headings(text)

    if resolved == "delta":
        _check_delta(headings, result)
    else:
        _check_baseline(headings, result)

    return result


def check_spec_file(path: Path, output_type: str = "auto") -> SpecFormatResult:
    """Read a spec file and check it; a missing file is itself a failure."""
    if not path.exists():
        result = SpecFormatResult(path=path, output_type=output_type)
        result.failures.append(f"spec file not found: {path}")
        return result
    return check_spec_format(path.read_text(encoding="utf-8"), path, output_type)


def collect_specs(paths: list[Path]) -> list[Path]:
    """Expand each argument into spec files: a directory contributes `**/spec.md`."""
    found: list[Path] = []
    for p in paths:
        if p.is_dir():
            found.extend(sorted(p.rglob("spec.md")))
        else:
            found.append(p)
    return found


def main() -> int:
    """Parse argv, check every named spec, and report."""
    args = sys.argv[1:]
    output_type = "auto"

    if args and args[0] == "--type":
        if len(args) < 3 or args[1] not in ("baseline", "delta"):
            print("Usage: check_spec_format.py [--type baseline|delta] <path>...", file=sys.stderr)
            return 2
        output_type = args[1]
        args = args[2:]

    if not args:
        print("Usage: check_spec_format.py [--type baseline|delta] <path>...", file=sys.stderr)
        return 2

    specs = collect_specs([Path(a) for a in args])
    if not specs:
        print("no spec.md files found in the given paths", file=sys.stderr)
        return 2

    results = [check_spec_file(p, output_type) for p in specs]
    failed = [r for r in results if not r.passed]

    for r in results:
        status = "PASS" if r.passed else "FAIL"
        print(f"{status}  [{r.output_type}] {r.path}  reqs={r.requirement_count} scenarios={r.scenario_count}")
        for msg in r.failures:
            print(f"  - {msg}")

    print(f"\n{len(results) - len(failed)}/{len(results)} specs match the canonical format")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
