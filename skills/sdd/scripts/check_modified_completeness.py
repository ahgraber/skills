#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "markdown-it-py>=3.0",
# ]
# ///
"""Guard against compressed MODIFIED delta requirements.

`sdd-sync` replaces each MODIFIED requirement wholesale, so any baseline
`#### Scenario:` that a MODIFIED delta block omits is silently deleted at sync.
This checker compares every MODIFIED requirement in a change's delta specs
against the matching baseline requirement and FAILS (exit 1) when a baseline
scenario is absent from the delta block — the unambiguous silent-loss case.

Scope: this is a check on **scenario names only**. It does not diff requirement
body text, so loss of a body sub-clause (without losing a named scenario) is
NOT caught here — that judgment stays with the agent-run guard in sdd-sync /
sdd-verify. The script is the deterministic backstop for dropped scenarios.

Matching policy (deliberately asymmetric):
- Requirement names match case- and whitespace-insensitively. Tolerance here
  *increases* coverage (more deltas match a baseline = more gets checked); a
  match made only by normalization emits a note.
- Scenario drops are detected on exact (stripped) names. Tolerance here would
  *reduce* coverage — two near-duplicate baseline scenarios would collapse and a
  real drop could hide — so the diff is strict. The allowlist directive is still
  matched tolerantly.

Layout assumed (SDD standard):
  <specs_root>/specs/<capability>/spec.md                    # baseline
  <specs_root>/changes/<change>/specs/<capability>/spec.md   # delta

Usage:
  check_modified_completeness.py <specs_root>
  check_modified_completeness.py <specs_root> --change <change-name>

Robustness:
- Code-block extents are computed with a CommonMark parser (markdown-it-py), so
  `#### Scenario:` headings shown as examples inside fenced/nested/mixed code
  blocks are ignored rather than miscounted. An unclosed fence is reported as an
  error (exit 2) rather than silently swallowing later scenarios.
- Unreadable spec files (non-UTF8, a directory, etc.) are reported as errors
  (exit 2) — never an uncaught traceback.

Intentional scenario removal:
  Record a deliberate drop inside the MODIFIED requirement block, and document
  the rationale in design.md (sdd-spec-formats.md § 4):

      <!-- modified-removes: OldScenarioName, AnotherScenario -->

Stacked changes:
  A MODIFIED requirement with no matching baseline is a note, not a failure: a
  later change can MODIFY a requirement added by an earlier unsynced change. Re-run
  after the earlier stack syncs.

Exit codes: 0 clean (incl. no active changes) · 1 dropped baseline scenario ·
2 usage error, unreadable spec, or unclosed fence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import sys

from markdown_it import MarkdownIt

H2 = re.compile(r"^##\s+(.+?)\s*$")
REQUIREMENT = re.compile(r"^###\s+Requirement:\s+(.+?)\s*$")
SCENARIO = re.compile(r"^####\s+Scenario:\s+(.+?)\s*$")
ALLOW_DROP = re.compile(r"<!--\s*modified-removes:\s*(.+?)\s*-->")
PREVIOUSLY = re.compile(r"^>\s*Previously:")
CLOSE_FENCE = re.compile(r"^\s*(`{3,}|~{3,})\s*$")
MODIFIED_CANONICAL = re.compile(r"^##\s+MODIFIED\s+Requirements\s*$", re.MULTILINE)
MODIFIED_LOOSE = re.compile(r"^##\s+modified\b", re.IGNORECASE | re.MULTILINE)

_MD = MarkdownIt("commonmark")


def normalize(name: str) -> str:
    """Collapse internal whitespace and casefold for tolerant name matching."""
    return re.sub(r"\s+", " ", name.strip()).casefold()


def _code_line_indices(text: str, lines: list[str]) -> tuple[set[int], bool]:
    """Return (0-based line indices inside code blocks, unclosed-fence flag).

    Uses a CommonMark parser so nested, mixed, and indented code blocks are
    delimited correctly. A fence whose final line is not a closing fence marker
    ran to end-of-input (CommonMark consumes the rest) — flagged as unclosed.
    """
    code: set[int] = set()
    unclosed = False
    for token in _MD.parse(text):
        if token.type in {"fence", "code_block"} and token.map:
            start, end = token.map
            code.update(range(start, end))
            if token.type == "fence":
                last = lines[end - 1] if 0 <= end - 1 < len(lines) else ""
                if not CLOSE_FENCE.match(last):
                    unclosed = True
    return code, unclosed


@dataclass
class Requirement:
    name: str  # original display name (last seen if duplicated)
    scenarios: list[str] = field(default_factory=list)  # original, stripped
    allow_drops: set[str] = field(default_factory=set)
    has_previously: bool = False


@dataclass
class ParsedSpec:
    requirements: dict[str, Requirement]  # keyed by normalize(name)
    duplicate_names: list[str] = field(default_factory=list)
    unclosed_fence: bool = False


def parse_requirements(text: str, *, modified_only: bool) -> ParsedSpec:
    """Parse `### Requirement:` blocks and their `#### Scenario:` names.

    When modified_only is True, only requirements under a `## MODIFIED ...`
    H2 section are returned (delta specs). Otherwise every requirement is
    returned (baseline specs). Headings inside fenced code blocks are ignored.
    """
    lines = text.splitlines()
    code_lines, unclosed = _code_line_indices(text, lines)
    reqs: dict[str, Requirement] = {}
    duplicates: list[str] = []
    in_scope = not modified_only  # baseline: every requirement counts
    current: Requirement | None = None
    for idx, line in enumerate(lines):
        if idx in code_lines:
            continue
        h2 = H2.match(line)
        if h2:
            words = h2.group(1).split()
            first = words[0].upper() if words else ""
            in_scope = (first == "MODIFIED") if modified_only else True
            current = None
            continue
        req = REQUIREMENT.match(line)
        if req:
            if in_scope:
                display = req.group(1).strip()
                key = normalize(display)
                if key in reqs:
                    duplicates.append(display)
                current = Requirement(name=display)
                reqs[key] = current
            else:
                current = None
            continue
        if current is None:
            continue
        scen = SCENARIO.match(line)
        if scen:
            current.scenarios.append(scen.group(1).strip())
        if PREVIOUSLY.match(line):
            current.has_previously = True
        allow = ALLOW_DROP.search(line)
        if allow:
            for nm in re.split(r"[;,]", allow.group(1)):
                if nm.strip():
                    current.allow_drops.add(nm.strip())
    return ParsedSpec(requirements=reqs, duplicate_names=duplicates, unclosed_fence=unclosed)


@dataclass
class Finding:
    capability: str
    requirement: str
    dropped: list[str]


def _read(path: Path) -> tuple[str | None, str | None]:
    """Read text, returning (text, None) or (None, error message)."""
    try:
        return path.read_text(encoding="utf-8"), None
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"{path}: cannot read ({type(exc).__name__})"


def _diff_requirement(
    capability: str, delta_req: Requirement, baseline: dict[str, Requirement]
) -> tuple[Finding | None, list[str]]:
    """Compare one MODIFIED requirement to its baseline; return (finding_or_None, notes)."""
    notes: list[str] = []
    if not delta_req.has_previously:
        notes.append(f"{capability} / {delta_req.name}: missing '> Previously:' provenance line")
    key = normalize(delta_req.name)
    if key not in baseline:
        notes.append(
            f"{capability} / {delta_req.name}: MODIFIED requirement has no matching baseline "
            "(stacked change, or a rename that should be REMOVED+ADDED) — not checked"
        )
        return None, notes
    baseline_req = baseline[key]
    if baseline_req.name != delta_req.name:
        notes.append(
            f"{capability} / {delta_req.name}: matched baseline '{baseline_req.name}' by "
            "normalization — align the requirement names"
        )
    if len({normalize(s) for s in baseline_req.scenarios}) != len(baseline_req.scenarios):
        notes.append(
            f"{capability} / {delta_req.name}: baseline has near-duplicate scenario names "
            "(differ only by case/whitespace) — drop detection uses exact names"
        )
    delta_present = set(delta_req.scenarios)
    allowed_norm = {normalize(a) for a in delta_req.allow_drops}
    dropped = [
        s for s in baseline_req.scenarios if s not in delta_present and normalize(s) not in allowed_norm
    ]
    dropped = list(dict.fromkeys(dropped))  # de-dupe, preserve order
    if dropped:
        return Finding(capability, delta_req.name, dropped), notes
    return None, notes


def check_change(
    specs_root: Path, change_dir: Path
) -> tuple[list[Finding], list[str], list[str]]:
    """Check one change's delta specs against the baseline.

    Returns (failures, notes, errors). failures are dropped-scenario cases only.
    """
    failures: list[Finding] = []
    notes: list[str] = []
    errors: list[str] = []
    specs_dir = change_dir / "specs"
    if not specs_dir.is_dir():
        return failures, notes, errors

    flat = set(specs_dir.glob("*/spec.md"))
    for stray in sorted(set(specs_dir.glob("**/spec.md")) - flat):
        notes.append(
            f"{stray.relative_to(specs_dir)}: spec.md below the expected <capability>/spec.md depth — not checked"
        )

    for delta_path in sorted(flat):
        capability = delta_path.parent.name
        delta_text, err = _read(delta_path)
        if delta_text is None:
            errors.append(err or f"{delta_path}: unreadable")
            continue
        parsed = parse_requirements(delta_text, modified_only=True)
        if parsed.unclosed_fence:
            errors.append(f"{delta_path}: unclosed code fence — cannot reliably parse")
            continue
        modified = parsed.requirements
        if not modified:
            continue
        if MODIFIED_LOOSE.search(delta_text) and not MODIFIED_CANONICAL.search(delta_text):
            notes.append(
                f"{capability}: non-canonical MODIFIED heading — expected '## MODIFIED Requirements'"
            )
        for dup in parsed.duplicate_names:
            notes.append(f"{capability}: duplicate MODIFIED requirement '{dup}' — only the last is checked")
        baseline_path = specs_root / "specs" / capability / "spec.md"
        if not baseline_path.exists():
            notes.append(
                f"{capability}: MODIFIED requirements present but no baseline spec yet at "
                f"{baseline_path} (stacked change? re-run after the earlier stack syncs) — not checked"
            )
            continue
        baseline_text, err = _read(baseline_path)
        if baseline_text is None:
            errors.append(err or f"{baseline_path}: unreadable")
            continue
        baseline_parsed = parse_requirements(baseline_text, modified_only=False)
        if baseline_parsed.unclosed_fence:
            errors.append(f"{baseline_path}: unclosed code fence — cannot reliably parse")
            continue
        baseline = baseline_parsed.requirements
        for dup in baseline_parsed.duplicate_names:
            notes.append(
                f"{capability}: duplicate baseline requirement '{dup}' — only the last is checked against"
            )
        for delta_req in modified.values():
            finding, req_notes = _diff_requirement(capability, delta_req, baseline)
            notes.extend(req_notes)
            if finding is not None:
                failures.append(finding)
    return failures, notes, errors


def discover_changes(specs_root: Path, change: str | None) -> list[Path]:
    """Return change directories to check: one if `change` is given, else all active."""
    changes_root = specs_root / "changes"
    if not changes_root.is_dir():
        return []
    if change:
        target = changes_root / change
        return [target] if target.is_dir() else []
    return sorted(p for p in changes_root.iterdir() if p.is_dir())


def main(argv: list[str]) -> int:
    """Parse args, run the check across the requested change(s), and return an exit code."""
    change: str | None = None
    positional: list[str] = []
    i = 0
    while i < len(argv):
        if argv[i] == "--change":
            if i + 1 >= len(argv):
                print("error: --change requires a value", file=sys.stderr)
                return 2
            change = argv[i + 1]
            i += 2
            continue
        positional.append(argv[i])
        i += 1

    if len(positional) != 1:
        print(
            "Usage: check_modified_completeness.py <specs_root> [--change <name>]",
            file=sys.stderr,
        )
        return 2
    specs_root = Path(positional[0])
    if not specs_root.exists():
        print(f"error: specs root not found: {specs_root}", file=sys.stderr)
        return 2
    if not specs_root.is_dir():
        print(f"error: specs root is not a directory: {specs_root}", file=sys.stderr)
        return 2

    change_dirs = discover_changes(specs_root, change)
    if not change_dirs:
        changes_root = specs_root / "changes"
        if change:
            print(f"error: change '{change}' not found under {changes_root}", file=sys.stderr)
            return 2
        print(f"no active changes under {changes_root} — nothing to check")
        return 0

    failures: list[Finding] = []
    notes: list[str] = []
    errors: list[str] = []
    for change_dir in change_dirs:
        change_failures, change_notes, change_errors = check_change(specs_root, change_dir)
        failures.extend(change_failures)
        notes.extend(f"{change_dir.name}: {note}" for note in change_notes)
        errors.extend(f"{change_dir.name}: {err}" for err in change_errors)

    for finding in failures:
        print(
            f"FAIL  [{finding.capability}] {finding.requirement}: "
            f"baseline scenario(s) absent from MODIFIED delta block: {', '.join(finding.dropped)}"
        )
    for err in errors:
        print(f"ERROR {err}")
    for note in notes:
        print(f"note  {note}")

    if errors:
        summary = f"{len(errors)} spec(s) could not be read or parsed — run is incomplete"
        if failures:
            summary += f"; {len(failures)} dropped-scenario failure(s) were ALSO found above"
        print(f"\n{summary}. Fix and re-run.")
        return 2
    if failures:
        print(
            f"\n{len(failures)} MODIFIED completeness failure(s) across {len(change_dirs)} change(s).\n"
            "A MODIFIED delta block must restate the complete post-change requirement "
            "(sdd-spec-formats.md § 4). Restore the dropped scenarios, or mark intentional "
            "removals with '<!-- modified-removes: ... -->' and document why in design.md."
        )
        return 1

    print(f"PASS  all MODIFIED requirements preserve baseline scenarios ({len(change_dirs)} change(s) checked).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
