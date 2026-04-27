from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
import hashlib
import logging
from pathlib import Path

from skills_mcp.discovery import RootSpec

logger = logging.getLogger("skills_mcp.dedup")


@dataclass(frozen=True)
class ResolvedSkill:
    """A skill folder that survived deduplication and should be exposed."""

    display_name: str  # Name used in `skill://{display_name}/...` URIs.
    root_label: str  # Label of the root the skill came from.
    skill_dir: Path  # Resolved on-disk directory.
    namespaced: bool  # True if the bare name was already taken.


def _hash_main_file(skill_dir: Path, main_file_name: str) -> str | None:
    """Return SHA-256 of the main skill file, or None if missing/unreadable."""
    main = skill_dir / main_file_name
    try:
        h = hashlib.sha256()
        with main.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def _iter_skill_dirs(root: Path, main_file_name: str) -> Iterator[Path]:
    """Yield first-level subdirectories of `root` that contain `main_file_name`."""
    try:
        entries = sorted(root.iterdir())
    except OSError:
        return
    for entry in entries:
        if not entry.is_dir():
            continue
        if not (entry / main_file_name).exists():
            continue
        yield entry


def dedup_skills(
    roots: list[RootSpec],
    *,
    main_file_name: str = "SKILL.md",
) -> list[ResolvedSkill]:
    """Walk roots in precedence order; collapse duplicates, namespace true collisions.

    Pipeline per skill name:
        1. Collect all `(root_label, resolved_dir)` pairs across roots.
        2. Group by realpath -> silently collapse symlink/inode duplicates.
        3. Hash SKILL.md per distinct realpath -> silently collapse byte-identical
           content (different paths, same SKILL.md).
        4. If multiple hash groups remain, keep the first-precedence one with the
           bare name. Each *additional* hash group emits one warning and is
           exposed under a namespaced display name `{root_label}--{name}`.
    """
    # Step 1: gather all candidates per canonical name, in precedence order.
    candidates: dict[str, list[tuple[str, Path]]] = defaultdict(list)
    for root in roots:
        for skill_dir in _iter_skill_dirs(root.path, main_file_name):
            candidates[skill_dir.name].append((root.label, skill_dir.resolve()))

    resolved: list[ResolvedSkill] = []
    used_display_names: set[str] = set()
    collapsed_symlinks = collapsed_hash = 0

    for canonical_name in sorted(candidates):
        entries = candidates[canonical_name]

        # Step 2: collapse by realpath (preserves first-seen label order).
        seen_paths: set[Path] = set()
        unique_by_path: list[tuple[str, Path]] = []
        for label, path in entries:
            if path in seen_paths:
                collapsed_symlinks += 1
                continue
            seen_paths.add(path)
            unique_by_path.append((label, path))

        # Step 3: collapse by SKILL.md hash (preserves first-seen group order).
        seen_hashes: dict[str, tuple[str, Path]] = {}
        ordered_groups: list[tuple[str, str, Path]] = []
        for label, path in unique_by_path:
            digest = _hash_main_file(path, main_file_name)
            if digest is None:
                logger.warning("Could not read %s for skill '%s' at %s", main_file_name, canonical_name, path)
                continue
            if digest in seen_hashes:
                collapsed_hash += 1
                continue
            seen_hashes[digest] = (label, path)
            ordered_groups.append((digest, label, path))

        if not ordered_groups:
            continue

        # Step 4: first group wins the bare name; subsequent groups get namespaced.
        _first_digest, first_label, first_path = ordered_groups[0]
        resolved.append(
            ResolvedSkill(
                display_name=canonical_name,
                root_label=first_label,
                skill_dir=first_path,
                namespaced=False,
            )
        )
        used_display_names.add(canonical_name)

        if len(ordered_groups) > 1:
            collision_labels = [first_label]
            for _digest, label, path in ordered_groups[1:]:
                base = f"{label}--{canonical_name}"
                display = base
                n = 2
                while display in used_display_names:
                    display = f"{base}{n}"
                    n += 1
                used_display_names.add(display)
                resolved.append(
                    ResolvedSkill(
                        display_name=display,
                        root_label=label,
                        skill_dir=path,
                        namespaced=True,
                    )
                )
                collision_labels.append(label)
            logger.warning(
                "Skill name collision: '%s' has differing content across roots %s; "
                "exposing first as bare name and others under namespaced URIs.",
                canonical_name,
                collision_labels,
            )

    logger.debug(
        "Dedup: resolved %d skills (collapsed %d symlinked, %d byte-identical)",
        len(resolved), collapsed_symlinks, collapsed_hash,
    )
    return resolved
