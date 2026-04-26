from __future__ import annotations

from collections.abc import Sequence
import logging
from pathlib import Path
from typing import Literal

from fastmcp.server.providers.skills.directory_provider import SkillsDirectoryProvider
from fastmcp.server.providers.skills.skill_provider import SkillProvider

from skills_mcp.dedup import DedupReport, ResolvedSkill, dedup_skills
from skills_mcp.discovery import RootSpec

logger = logging.getLogger("skills_mcp.provider")


class NamespacedSkillProvider(SkillProvider):
    """`SkillProvider` whose exposed `skill://{name}/...` is overridden post-load.

    Used to expose colliding skills under namespaced URIs without renaming
    anything on disk.
    """

    def __init__(
        self,
        skill_path: str | Path,
        *,
        display_name: str,
        main_file_name: str = "SKILL.md",
        supporting_files: Literal["template", "resources"] = "template",
    ) -> None:
        super().__init__(
            skill_path=skill_path,
            main_file_name=main_file_name,
            supporting_files=supporting_files,
        )
        # SkillInfo is a plain dataclass; mutating `name` here changes the URI
        # advertised by all subsequent `_list_resources` / `_get_resource` calls.
        if self._skill_info is not None:
            self._skill_info.name = display_name


class DedupSkillsDirectoryProvider(SkillsDirectoryProvider):
    """`SkillsDirectoryProvider` with realpath/hash dedup and namespaced collisions.

    Replaces the upstream name-only first-wins logic with a three-step pipeline
    (see `skills_mcp.dedup.dedup_skills`).
    """

    def __init__(
        self,
        roots: Sequence[RootSpec],
        *,
        reload: bool = False,
        main_file_name: str = "SKILL.md",
        supporting_files: Literal["template", "resources"] = "template",
        namespace_separator: str = "--",
    ) -> None:
        self._root_specs: list[RootSpec] = list(roots)
        self._namespace_separator = namespace_separator
        self._last_report: DedupReport | None = None
        # Hand the base class the bare paths so its bookkeeping (and __repr__)
        # still works; we then immediately replace what `_discover_skills`
        # produced with our deduplicated set.
        super().__init__(
            roots=[spec.path for spec in roots] or [Path.cwd()],
            reload=reload,
            main_file_name=main_file_name,
            supporting_files=supporting_files,
        )

    def _discover_skills(self) -> None:
        # Called by the base `__init__` before our attributes are set, and again
        # on reload. Skip the first call - our `__init__` runs `_run_dedup` once
        # the base class is done.
        if not hasattr(self, "_root_specs"):
            self.providers.clear()
            return
        self._run_dedup()

    def _run_dedup(self) -> None:
        self.providers.clear()
        report = dedup_skills(
            self._root_specs,
            main_file_name=self._main_file_name,
            namespace_separator=self._namespace_separator,
        )
        self._last_report = report

        for resolved in report.resolved:
            try:
                provider = self._build_provider(resolved)
            except (FileNotFoundError, PermissionError, OSError):
                logger.exception("Failed to load skill: %s", resolved.skill_dir)
                continue
            self.providers.append(provider)

        self._discovered = True
        logger.info(
            "Loaded %d skills (collapsed %d symlinked, %d byte-identical, %d collisions namespaced)",
            len(self.providers),
            report.collapsed_symlinks,
            report.collapsed_hash,
            len(report.namespace_collisions),
        )

    def _build_provider(self, resolved: ResolvedSkill) -> SkillProvider:
        if resolved.namespaced:
            return NamespacedSkillProvider(
                skill_path=resolved.skill_dir,
                display_name=resolved.display_name,
                main_file_name=self._main_file_name,
                supporting_files=self._supporting_files,
            )
        return SkillProvider(
            skill_path=resolved.skill_dir,
            main_file_name=self._main_file_name,
            supporting_files=self._supporting_files,
        )

    @property
    def last_report(self) -> DedupReport | None:
        """Most recent dedup report (None until first discovery completes)."""
        return self._last_report

    def __repr__(self) -> str:
        return (
            f"DedupSkillsDirectoryProvider("
            f"roots={[r.label for r in self._root_specs]}, "
            f"skills={len(self.providers)})"
        )
