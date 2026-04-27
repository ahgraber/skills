from skills_mcp.dedup import ResolvedSkill, dedup_skills
from skills_mcp.discovery import KNOWN_ROOTS, RootSpec, discover_roots
from skills_mcp.provider import DedupSkillsDirectoryProvider, NamespacedSkillProvider
from skills_mcp.server import build_server, main

__all__ = [
    "KNOWN_ROOTS",
    "DedupSkillsDirectoryProvider",
    "NamespacedSkillProvider",
    "ResolvedSkill",
    "RootSpec",
    "build_server",
    "dedup_skills",
    "discover_roots",
    "main",
]
