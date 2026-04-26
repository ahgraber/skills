from __future__ import annotations

from pathlib import Path

import pytest


def _write_skill(root: Path, name: str, body: str = "Body.\n") -> Path:
    skill_dir = root / name
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test skill {name}\n---\n\n{body}",
        encoding="utf-8",
    )
    return skill_dir


@pytest.fixture
def make_skill():
    """Create a skill folder under a given root directory."""
    return _write_skill
