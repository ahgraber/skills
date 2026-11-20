#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8",
#   "pyyaml>=6.0",
# ]
# ///
"""Guard: no skill description contains `<` or `>`.

claude.ai reads angle brackets in a SKILL.md description as XML tags, reports the
skill as invalid, and stores the description with the brackets removed. Claude Code
reads the full text from the file, so the skill still loads there; the failure shows
only on claude.ai.
"""

from pathlib import Path
import yaml

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILLS = REPO / "skills"


def _skill_files() -> list[Path]:
    return sorted(SKILLS.glob("*/SKILL.md"))


def _description(path: Path) -> str:
    _, front, _ = path.read_text(encoding="utf-8").split("---", 2)
    return str(yaml.safe_load(front).get("description", ""))


def test_skills_are_found():
    assert _skill_files(), f"no SKILL.md files under {SKILLS}"


@pytest.mark.parametrize("path", _skill_files(), ids=lambda p: p.parent.name)
def test_description_has_no_angle_brackets(path: Path):
    description = _description(path)
    assert "<" not in description, description
    assert ">" not in description, description


if __name__ == "__main__":
    _here = str(Path(__file__).resolve().parent)
    raise SystemExit(
        pytest.main(
            [str(Path(__file__).resolve()), "-q", "-p", "no:cacheprovider", "--rootdir", _here, "--confcutdir", _here]
        )
    )
