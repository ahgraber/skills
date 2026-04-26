from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RootSpec:
    """A skills root with a short label used for namespaced URIs."""

    label: str
    path: Path


HOME = Path.home()

KNOWN_ROOTS: tuple[RootSpec, ...] = (
    RootSpec("project", Path.cwd() / ".claude" / "skills"),
    RootSpec("agents", HOME / ".agents" / "skills"),
    RootSpec("claude", HOME / ".claude" / "skills"),
    RootSpec("cursor", HOME / ".cursor" / "skills"),
    RootSpec("codex", HOME / ".codex" / "skills"),
    RootSpec("gemini", HOME / ".gemini" / "skills"),
    RootSpec("copilot", HOME / ".copilot" / "skills"),
    RootSpec("opencode", HOME / ".config" / "opencode" / "skills"),
    RootSpec("goose", HOME / ".config" / "agents" / "skills"),
)

ENV_VAR = "SKILLS_MCP_ROOTS"


def _label_safe(label: str) -> str:
    """Reduce an arbitrary label to characters safe inside a `skill://` path component."""
    cleaned = "".join(c if c.isalnum() or c in "-_." else "-" for c in label)
    return cleaned.strip("-") or "extra"


def _label_from_path(path: Path) -> str:
    """Derive a short label from a path's tail components."""
    parts = [p for p in path.parts if p not in ("", "/")]
    if not parts:
        return "extra"
    tail = parts[-1]
    if tail in {"skills", "skill"} and len(parts) >= 2:
        tail = parts[-2]
    return _label_safe(tail.lstrip("."))


def parse_root_arg(arg: str) -> RootSpec:
    """Parse a `--root` CLI value of the form `LABEL=PATH` or `PATH`."""
    if "=" in arg:
        label, _, raw = arg.partition("=")
        label = _label_safe(label.strip())
        path = Path(raw.strip()).expanduser()
    else:
        path = Path(arg).expanduser()
        label = _label_from_path(path)
    return RootSpec(label=label, path=path)


def parse_env_roots(value: str | None = None) -> list[RootSpec]:
    """Parse the `SKILLS_MCP_ROOTS` env var (colon-separated PATH or LABEL=PATH entries)."""
    raw = value if value is not None else os.environ.get(ENV_VAR, "")
    if not raw:
        return []
    return [parse_root_arg(entry) for entry in raw.split(os.pathsep) if entry.strip()]


def discover_roots(
    *,
    extra: Iterable[RootSpec] = (),
    include_known: bool = True,
    include_env: bool = True,
    include_labels: Iterable[str] | None = None,
    exclude_labels: Iterable[str] = (),
    require_exists: bool = True,
) -> list[RootSpec]:
    """Resolve the ordered list of skill roots to scan.

    Precedence (later entries lose name collisions to earlier ones):
        1. extra (CLI `--root`)
        2. env (`SKILLS_MCP_ROOTS`)
        3. KNOWN_ROOTS (vendor defaults), filtered by include/exclude

    Args:
        extra: Roots from CLI, applied in given order at the front.
        include_known: Include vendor defaults from KNOWN_ROOTS.
        include_env: Read `SKILLS_MCP_ROOTS` env var.
        include_labels: If set, restrict KNOWN_ROOTS to these labels.
        exclude_labels: Drop these labels from KNOWN_ROOTS.
        require_exists: Drop entries whose path does not exist.

    Returns
    -------
        Roots in precedence order, deduplicated by resolved path.
    """
    ordered: list[RootSpec] = []
    ordered.extend(extra)

    if include_env:
        ordered.extend(parse_env_roots())

    if include_known:
        include_set = set(include_labels) if include_labels is not None else None
        exclude_set = set(exclude_labels)
        for spec in KNOWN_ROOTS:
            if include_set is not None and spec.label not in include_set:
                continue
            if spec.label in exclude_set:
                continue
            ordered.append(spec)

    seen_real: set[Path] = set()
    used_labels: set[str] = set()
    result: list[RootSpec] = []
    for spec in ordered:
        path = spec.path.expanduser()
        if require_exists and not path.exists():
            continue
        try:
            real = path.resolve()
        except OSError:
            continue
        if real in seen_real:
            continue
        seen_real.add(real)

        # Disambiguate label collisions across equally-named user roots.
        label = spec.label
        if label in used_labels:
            n = 2
            while f"{label}{n}" in used_labels:
                n += 1
            label = f"{label}{n}"
        used_labels.add(label)

        result.append(RootSpec(label=label, path=real))
    return result
