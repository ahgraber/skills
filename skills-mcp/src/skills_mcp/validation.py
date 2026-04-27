"""Validate SKILL.md frontmatter against the agentskills.io specification, and sanitize skill content before it enters a prompt index.

Spec: https://agentskills.io/specification
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re
import yaml

# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

_FRONTMATTER_BLOCK_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---", re.DOTALL)
_FRONTMATTER_DESC_RE = re.compile(r"^description:\s*(.+?)$", re.MULTILINE)


def read_frontmatter_description(skill_path: Path) -> str | None:
    """Return the raw ``description:`` value from SKILL.md frontmatter, or None.

    Returns None when the field is absent, empty, or the file is unreadable.
    Deliberately ignores the skill body and FastMCP's synthesised fallbacks —
    we only trust what the skill author explicitly wrote in the frontmatter.

    Note: callers typically pass ``sp._skill_path``, a FastMCP private attribute.
    It is stable across all tested versions and is the only way to reach the raw
    file without re-running discovery.
    """
    try:
        text = (skill_path / "SKILL.md").read_text(encoding="utf-8")
    except OSError:
        return None
    fm = _FRONTMATTER_BLOCK_RE.match(text)
    if not fm:
        return None
    m = _FRONTMATTER_DESC_RE.search(fm.group(1))
    return m.group(1).strip() if m else None


def _parse_frontmatter(text: str) -> tuple[dict, None] | tuple[None, str]:
    """Return (parsed_dict, error_message). One of the two is always None."""
    m = _FRONTMATTER_BLOCK_RE.match(text)
    if not m:
        return None, "no YAML frontmatter block (expected --- ... ---)"
    try:
        data = yaml.safe_load(m.group(1))
    except yaml.YAMLError as exc:
        return None, f"YAML parse error: {exc}"
    if not isinstance(data, dict):
        return None, "frontmatter parsed to a non-mapping value"
    return data, None


# ---------------------------------------------------------------------------
# Sanitization — strip prompt-injection vectors before index inclusion
# ---------------------------------------------------------------------------

# Unicode invisible characters: Tag Block (U+E0000–U+E007F), zero-width chars
# (U+200B–U+200D, U+2060, U+FEFF), and variation selectors (U+FE00–U+FE0F).
# These pass visually as empty space but LLMs may decode and act on them.
_UNICODE_INVISIBLE_RE = re.compile(r"[​-‍⁠﻿︀-️\U000e0000-\U000e007f]")
# ChatML / Llama-3 special tokens: <|...|>, <|begin_of_text|>, <|eot_id|>, etc.
# Must be stripped before the angle-bracket pass so the full pattern is matched.
_SPECIAL_TOKEN_RE = re.compile(r"<\|[^|>\n]{0,40}\|>")
# Bracket-delimited instruction tokens used by Llama-2 / Mistral:
# [INST], [/INST], <<SYS>>, <</SYS>>, [AVAILABLE_TOOLS], [TOOL_RESULTS], etc.
_BRACKET_TOKEN_RE = re.compile(
    r"\[/?(?:INST|SYS|AVAILABLE_TOOLS|TOOL_CALLS|TOOL_RESULTS)\]"
    r"|<{1,2}/?SYS>{1,2}",
    re.IGNORECASE,
)
# Markdown link / HTML-tag forming characters: must run after the pattern passes above.
_MARKDOWN_LINK_CHARS_RE = re.compile(r"[\[\]()<>]")


def sanitize_description(text: str) -> str:
    """Strip prompt-injection vectors from a skill description before it enters the index.

    Layers (applied in order — earlier passes remove structured patterns before
    individual-character passes would fragment them):
      1. Unicode invisible / zero-width characters
      2. ChatML special tokens  (<|im_start|> etc.)
      3. Bracket-delimited instruction tokens ([INST], <<SYS>>, …)
      4. Remaining Markdown link / HTML characters ([]()<>)
      5. Bold markers and newline normalisation
    """
    text = _UNICODE_INVISIBLE_RE.sub("", text)
    text = _SPECIAL_TOKEN_RE.sub("", text)
    text = _BRACKET_TOKEN_RE.sub("", text)
    text = _MARKDOWN_LINK_CHARS_RE.sub("", text)
    text = text.replace("**", "").strip().replace("\n", " ")
    return text


# ---------------------------------------------------------------------------
# Index-safety name check
# ---------------------------------------------------------------------------

# Broader than the spec regex — allows uppercase / spaces / dots that may appear
# in FastMCP's synthesised names, which don't always come from the directory name.
SAFE_SKILL_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9 ._-]{0,63}$")


# ---------------------------------------------------------------------------
# Spec validation
# ---------------------------------------------------------------------------

# name: lowercase letters, numbers, hyphens only; 1-64 chars;
# no leading/trailing/consecutive hyphens.
_NAME_CHARS_RE = re.compile(r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$")
_CONSECUTIVE_HYPHENS_RE = re.compile(r"--")


@dataclass
class ValidationIssue:
    field: str
    message: str
    severity: str = "error"  # "error" | "warning"

    def __str__(self) -> str:
        return f"[{self.severity.upper()}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    skill_dir: Path
    issues: list[ValidationIssue] = field(default_factory=list)
    sanitized_description: str | None = None

    @property
    def valid(self) -> bool:
        """Return True when the result contains no error-severity issues."""
        return not any(i.severity == "error" for i in self.issues)

    def __str__(self) -> str:
        status = "OK" if self.valid else "FAIL"
        lines = [f"{status}  {self.skill_dir}"]
        for issue in self.issues:
            lines.append(f"       {issue}")
        return "\n".join(lines)


def _too_long(field: str, value: str, max_len: int) -> ValidationIssue | None:
    if len(value) > max_len:
        return ValidationIssue(field, f"too long ({len(value)} chars, max {max_len})")
    return None


def _check_name(fm: dict, dir_name: str) -> list[ValidationIssue]:
    name = fm.get("name")
    if not name:
        return [ValidationIssue("name", "required field is missing or empty")]
    name = str(name)
    issues: list[ValidationIssue] = []
    if issue := _too_long("name", name, 64):
        issues.append(issue)
    if not _NAME_CHARS_RE.match(name):
        issues.append(ValidationIssue(
            "name",
            f"invalid: only lowercase letters, digits, and hyphens allowed; "
            f"must not start or end with a hyphen — got {name!r}",
        ))
    elif _CONSECUTIVE_HYPHENS_RE.search(name):
        issues.append(ValidationIssue("name", f"consecutive hyphens not allowed in {name!r}"))
    if name != dir_name:
        issues.append(ValidationIssue(
            "name", f"name field {name!r} does not match directory name {dir_name!r}"
        ))
    return issues


def _check_description(fm: dict) -> list[ValidationIssue]:
    desc = fm.get("description")
    if not desc:
        return [ValidationIssue("description", "required field is missing or empty")]
    if issue := _too_long("description", str(desc), 1024):
        return [issue]
    return []


def _check_optional_fields(fm: dict) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    compat = fm.get("compatibility")
    if compat is not None and (issue := _too_long("compatibility", str(compat), 500)):
        issues.append(issue)
    if (metadata := fm.get("metadata")) is not None and not isinstance(metadata, dict):
        issues.append(ValidationIssue("metadata", "must be a key-value mapping"))
    if (allowed := fm.get("allowed-tools")) is not None and not isinstance(allowed, str):
        issues.append(ValidationIssue("allowed-tools", "must be a space-separated string"))
    return issues


def _extract_sanitized_description(text: str) -> str | None:
    # Uses regex rather than YAML so it survives malformed frontmatter
    # (e.g. `[INST]` is a valid YAML flow sequence and breaks safe_load).
    fm_block = _FRONTMATTER_BLOCK_RE.match(text)
    if not fm_block:
        return None
    m = _FRONTMATTER_DESC_RE.search(fm_block.group(1))
    return sanitize_description(m.group(1).strip()) or None if m else None


def validate_skill(skill_dir: Path) -> ValidationResult:
    """Validate a single skill directory against the agentskills.io spec."""
    result = ValidationResult(skill_dir=skill_dir)

    try:
        text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    except FileNotFoundError:
        result.issues.append(ValidationIssue("SKILL.md", "file is missing"))
        return result
    except OSError as exc:
        result.issues.append(ValidationIssue("SKILL.md", f"cannot read file: {exc}"))
        return result

    result.sanitized_description = _extract_sanitized_description(text)

    fm, err = _parse_frontmatter(text)
    if err:
        result.issues.append(ValidationIssue("frontmatter", err))
        return result

    result.issues.extend(_check_name(fm, skill_dir.name))
    result.issues.extend(_check_description(fm))
    result.issues.extend(_check_optional_fields(fm))
    return result


def validate_skills(paths: list[Path]) -> list[ValidationResult]:
    """Validate each path in *paths* and return one result per skill directory."""
    return [validate_skill(p) for p in paths]
