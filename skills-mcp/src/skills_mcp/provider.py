from __future__ import annotations

from collections.abc import Sequence
import logging
from pathlib import Path

from fastmcp.server.providers.skills.directory_provider import SkillsDirectoryProvider
from fastmcp.server.providers.skills.skill_provider import SkillProvider

from skills_mcp.dedup import ResolvedSkill, dedup_skills
from skills_mcp.discovery import RootSpec
from skills_mcp.validation import SAFE_SKILL_NAME_RE, ValidationResult, validate_skill

logger = logging.getLogger("skills_mcp.provider")


class NamespacedSkillProvider(SkillProvider):
    """`SkillProvider` whose exposed `skill://{name}/...` is overridden post-load.

    Used to expose colliding skills under namespaced URIs without renaming
    anything on disk.
    """

    def __init__(self, skill_path: str | Path, *, display_name: str) -> None:
        super().__init__(skill_path=skill_path)
        # SkillInfo is a plain dataclass; mutating `name` here changes the URI
        # advertised by all subsequent `_list_resources` / `_get_resource` calls.
        if self._skill_info is None:
            raise RuntimeError(
                f"SkillProvider loaded {skill_path!r} without _skill_info; FastMCP API may have changed"
            )
        self._skill_info.name = display_name


class DedupSkillsDirectoryProvider(SkillsDirectoryProvider):
    """`SkillsDirectoryProvider` with realpath/hash dedup and namespaced collisions.

    Replaces the upstream name-only first-wins logic with a three-step pipeline
    (see `skills_mcp.dedup.dedup_skills`).
    """

    def __init__(self, roots: Sequence[RootSpec], *, reload: bool = False) -> None:
        self._root_specs: list[RootSpec] = list(roots)
        self.validations: dict[Path, ValidationResult] = {}
        # Hand the base class the bare paths so its bookkeeping (and __repr__)
        # still works; we then immediately replace what `_discover_skills`
        # produced with our deduplicated set.
        super().__init__(
            roots=[spec.path for spec in roots] or [Path.cwd()],
            reload=reload,
        )

    def _discover_skills(self) -> None:
        self.providers.clear()
        self.validations.clear()
        for resolved in dedup_skills(self._root_specs, main_file_name=self._main_file_name):
            validation = validate_skill(resolved.skill_dir)
            if not validation.valid:
                logger.warning(
                    "Skill %r loaded with errors: %s",
                    resolved.display_name,
                    "; ".join(str(i) for i in validation.issues),
                )
            try:
                provider = self._build_provider(resolved)
            except (OSError, RuntimeError):
                logger.exception("Failed to load skill: %s", resolved.skill_dir)
                continue
            name = (provider.skill_info.name or "").strip()
            if not SAFE_SKILL_NAME_RE.fullmatch(name):
                logger.warning("Skipping skill: display name %r failed safety check", name)
                continue
            self.validations[resolved.skill_dir] = validation
            self.providers.append(provider)
        self._discovered = True
        logger.info("Loaded %d skills", len(self.providers))

    def _build_provider(self, resolved: ResolvedSkill) -> SkillProvider:
        if resolved.display_name != resolved.skill_dir.name:
            return NamespacedSkillProvider(skill_path=resolved.skill_dir, display_name=resolved.display_name)
        return SkillProvider(skill_path=resolved.skill_dir)

    def __repr__(self) -> str:
        return (
            f"DedupSkillsDirectoryProvider("
            f"roots={[r.label for r in self._root_specs]}, "
            f"skills={len(self.providers)})"
        )
