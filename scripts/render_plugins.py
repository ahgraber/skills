#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""Render the plugins declared in plugins.yaml into the Claude Code plugin layout.

Writes `plugins/<plugin>/.claude-plugin/plugin.json`, a README, the shared icon, and a
copy of each listed skill per plugin, plus the repo-root `.claude-plugin/marketplace.json`
catalog. Claude Code, Codex, and Copilot CLI all install from these files.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import yaml

# plugins.yaml names transports as the Agent Plugins spec does; Claude Code calls
# remote Streamable HTTP `http`.
CLAUDE_TRANSPORTS = {"streamable-http": "http", "sse": "sse", "stdio": "stdio"}

# plugins.yaml uses the Agent Plugins placeholders; Claude Code prefixes both.
CLAUDE_PLACEHOLDERS = {"${PLUGIN_ROOT}": "${CLAUDE_PLUGIN_ROOT}", "${PLUGIN_DATA}": "${CLAUDE_PLUGIN_DATA}"}

# Metadata fields copied from plugins.yaml into each manifest, in output order.
MANIFEST_FIELDS = ("name", "version", "description", "author", "homepage", "repository", "license", "keywords")

# Build and OS droppings that live beside a skill but are untracked. Copying them
# would make a rendered tree depend on the local machine, so --check would drift
# against a fresh clone.
SKIP_NAMES = frozenset({"__pycache__", ".DS_Store", ".pytest_cache", ".ruff_cache", ".ipynb_checkpoints"})
SKIP_SUFFIXES = (".pyc", ".pyo")

# The first sentence of a skill description, which states when to use the skill. A
# period followed by a lowercase word, as in "e.g. this", does not end the sentence.
FIRST_SENTENCE = re.compile(r"(.+?[.!?])(?=\s+[^a-z]|$)")

# Claude Code finds a plugin's icon at this path without a manifest field.
ICON_PATH = Path(".claude-plugin") / "icon.png"

GENERATED_README = """\
# Generated plugins

Everything in this directory is rendered by `scripts/render_plugins.py` from
`plugins.yaml` at the repository root. Edit the skill under `skills/` or the
plugin definition in `plugins.yaml`, then run `just render-plugins`.

Hand edits here are overwritten and fail `just check-plugins`.
"""


class RenderError(Exception):
    """A manifest or skill-tree problem that stops rendering."""


# --- manifest ---------------------------------------------------------------


def load_manifest(path: Path) -> dict:
    """Parse plugins.yaml and check the keys the renderer depends on."""
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RenderError(f"{path} must contain a mapping")
    for key in ("version", "marketplace", "plugins"):
        if key not in data:
            raise RenderError(f"{path} is missing required key: {key}")
    if not isinstance(data["plugins"], dict) or not data["plugins"]:
        raise RenderError(f"{path}: 'plugins' must be a non-empty mapping")
    return data


def validate_coverage(manifest: dict, skills_root: Path) -> None:
    """Require every skill on disk to sit in exactly one plugin or in `unbundled`."""
    on_disk = {path.name for path in skills_root.iterdir() if (path / "SKILL.md").is_file()}
    unbundled = set(manifest.get("unbundled") or [])

    placements: dict[str, list[str]] = defaultdict(list)
    for plugin, spec in manifest["plugins"].items():
        skills = spec.get("skills") or []
        if not skills:
            raise RenderError(f"plugin '{plugin}' lists no skills")
        for skill in skills:
            placements[skill].append(plugin)

    problems = []
    for skill, plugins in sorted(placements.items()):
        if len(plugins) > 1:
            problems.append(f"skill '{skill}' appears in more than one plugin: {', '.join(plugins)}")
        if skill in unbundled:
            problems.append(f"skill '{skill}' is listed in 'unbundled' and in plugin '{plugins[0]}'")
    problems += [f"unknown skill '{s}' (no skills/{s}/SKILL.md)" for s in sorted(set(placements) - on_disk)]
    problems += [f"unknown skill '{s}' in 'unbundled' (no skills/{s}/SKILL.md)" for s in sorted(unbundled - on_disk)]
    problems += [
        f"skill '{s}' is in no plugin; add it to a plugin or to 'unbundled'"
        for s in sorted(on_disk - set(placements) - unbundled)
    ]
    if problems:
        raise RenderError("plugins.yaml does not cover skills/ correctly:\n  - " + "\n  - ".join(problems))


def validate_dependencies(manifest: dict) -> None:
    """Require each dependency to name another plugin in this catalog."""
    plugins = manifest["plugins"]
    problems = []
    for plugin, spec in plugins.items():
        for dependency in spec.get("dependencies") or []:
            if dependency == plugin:
                problems.append(f"plugin '{plugin}' depends on itself")
            elif dependency not in plugins:
                problems.append(f"plugin '{plugin}' depends on unknown plugin '{dependency}'")
    if problems:
        raise RenderError("plugins.yaml has bad dependencies:\n  - " + "\n  - ".join(problems))


# --- skill tree -------------------------------------------------------------


def tracked_paths(root: Path) -> set[Path] | None:
    """Return the paths git tracks under `skills/`, or None outside a git checkout.

    A rendered plugin must mirror what ships. Untracked files beside a skill, such
    as a large reference PDF someone downloaded, would otherwise be copied in and
    hashed, so `--check` would report drift against any clone that lacks them.
    """
    try:
        listing = subprocess.run(  # noqa: S603
            ["git", "-C", str(root), "ls-files", "-z", "--", "skills"],
            capture_output=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return {root / name for name in listing.stdout.decode("utf-8").split("\0") if name}


def _ignore_droppings(_directory: str, names: list[str]) -> set[str]:
    """Name the entries `shutil.copytree` should leave behind."""
    return {name for name in names if name in SKIP_NAMES or name.endswith(SKIP_SUFFIXES)}


def copy_skill(src: Path, dst: Path, tracked: set[Path] | None = None) -> None:
    """Copy one skill into a plugin, writing each symlink as the content it points to.

    Codex drops symlinks when it copies a plugin into its cache, so a linked file
    would be missing for Codex users.
    """
    dst.mkdir(parents=True, exist_ok=True)
    for entry in sorted(src.iterdir()):
        if entry.name in SKIP_NAMES or entry.name.endswith(SKIP_SUFFIXES):
            continue
        if tracked is not None and not entry.is_dir() and entry not in tracked:
            continue
        target = dst / entry.name
        if entry.is_symlink():
            resolved = entry.resolve()
            if not resolved.exists():
                raise RenderError(f"broken symlink: {entry} -> {os.readlink(entry)}")
            if resolved.is_dir():
                shutil.copytree(resolved, target, symlinks=False, ignore=_ignore_droppings)
            else:
                shutil.copy2(resolved, target)
        elif entry.is_dir():
            copy_skill(entry, target, tracked)
        else:
            shutil.copy2(entry, target)


# --- manifest rendering -----------------------------------------------------


def _metadata(manifest: dict, name: str, spec: dict) -> dict:
    """Merge the shared defaults with one plugin's own metadata."""
    merged = {**(manifest.get("defaults") or {})}
    merged["name"] = name
    merged["version"] = manifest["version"]
    for key in ("description", "category", "keywords"):
        if key in spec:
            merged[key] = spec[key]
    return merged


def _ordered(meta: dict, fields: tuple[str, ...]) -> dict:
    """Project a metadata mapping onto the given fields, dropping absent ones."""
    return {key: meta[key] for key in fields if key in meta}


def _claudeify(value: object) -> object:
    """Rewrite the neutral placeholders into their Claude Code spellings."""
    if isinstance(value, str):
        for source, replacement in CLAUDE_PLACEHOLDERS.items():
            value = value.replace(source, replacement)
        return value
    if isinstance(value, dict):
        return {key: _claudeify(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_claudeify(item) for item in value]
    return value


def claude_mcp_servers(servers: dict, overrides: dict) -> dict:
    """Map the neutral servers onto Claude Code's transports and placeholders, merging its extra fields."""
    rendered = {}
    for name, server in servers.items():
        transport = server.get("type")
        if transport not in CLAUDE_TRANSPORTS:
            raise RenderError(f"MCP server '{name}': unsupported type '{transport}'")
        entry = {**_claudeify(server), "type": CLAUDE_TRANSPORTS[transport]}
        entry.update(_claudeify(overrides.get(name, {})))
        rendered[name] = entry
    return rendered


def claude_plugin_manifest(meta: dict, spec: dict) -> dict:
    """Build `.claude-plugin/plugin.json` for one plugin.

    MCP servers go inline rather than into a sibling `.mcp.json`; Claude Code
    accepts either, and inline keeps them beside the `userConfig` they read.
    """
    out = _ordered(meta, MANIFEST_FIELDS)
    claude = spec.get("claude") or {}
    if spec.get("dependencies"):
        out["dependencies"] = list(spec["dependencies"])
    if claude.get("userConfig"):
        out["userConfig"] = claude["userConfig"]
    if spec.get("mcp"):
        out["mcpServers"] = claude_mcp_servers(spec["mcp"], claude.get("mcpServers") or {})
    if spec.get("privacy"):
        out["privacyPolicyUrl"] = spec["privacy"]
    return out


def marketplace_entry(meta: dict, plugin: str) -> dict:
    """Build one `plugins[]` entry for the marketplace catalog."""
    return {**_ordered(meta, MANIFEST_FIELDS), "source": f"./plugins/{plugin}", **_ordered(meta, ("category",))}


# --- plugin README ----------------------------------------------------------


def skill_summary(skill_md: Path) -> str:
    """Return the first sentence of a skill's description."""
    parts = skill_md.read_text(encoding="utf-8").split("---", 2)
    front = yaml.safe_load(parts[1]) if len(parts) == 3 and not parts[0].strip() else None
    description = " ".join(str((front or {}).get("description", "")).split())
    match = FIRST_SENTENCE.match(description)
    return match.group(1) if match else description


def _marketplace_source(manifest: dict) -> str:
    """Name the marketplace as `plugin marketplace add` takes it: owner/repo on GitHub, else the URL."""
    repository = str((manifest.get("defaults") or {}).get("repository", ""))
    return repository.removeprefix("https://github.com/") or manifest["marketplace"]["name"]


def plugin_readme(manifest: dict, plugin: str, spec: dict, skills_root: Path) -> str:
    """Build a plugin's README: what it holds, how to install it, and any MCP setup."""
    market = manifest["marketplace"]["name"]
    source = _marketplace_source(manifest)
    dependencies = list(spec.get("dependencies") or [])
    lines = [f"# {plugin}", ""]
    if spec.get("description"):
        lines += [spec["description"], ""]
    lines += [f"A plugin from the `{market}` marketplace for Claude Code, Codex, and GitHub Copilot.", ""]

    lines += ["## Skills", ""]
    lines += [f"- `{skill}`: {skill_summary(skills_root / skill / 'SKILL.md')}" for skill in sorted(spec["skills"])]
    lines.append("")

    lines += ["## Install", ""]
    if dependencies:
        named = ", ".join(f"`{name}`" for name in dependencies)
        lines += [
            f"Skills in this plugin call on the skills in {named}.",
            "Claude Code installs them with this plugin; in Codex and Copilot, install them yourself as shown.",
            "",
        ]
    lines += [
        "```bash",
        "# Claude Code",
        f"claude plugin marketplace add {source}",
        f"claude plugin install {plugin}@{market}",
        "",
        "# Codex",
        f"codex plugin marketplace add {source}",
        *[f"codex plugin add {name}@{market}" for name in [*dependencies, plugin]],
        "",
        "# GitHub Copilot CLI; VS Code picks up plugins installed this way",
        f"copilot plugin marketplace add {source}",
        *[f"copilot plugin install {name}@{market}" for name in [*dependencies, plugin]],
        "```",
        "",
    ]

    if spec.get("mcp"):
        lines += ["## MCP servers", "", "This plugin registers these MCP servers:", ""]
        lines += [
            f"- `{name}`: {server.get('url', server.get('command', ''))}" for name, server in spec["mcp"].items()
        ]
        lines.append("")
        if spec.get("privacy"):
            lines += [f"Privacy policy of the server provider: {spec['privacy']}", ""]
        settings = ((spec.get("claude") or {}).get("userConfig")) or {}
        if settings:
            lines += [
                f"In Claude Code, set these options in the `/plugin` menu or with `claude plugin configure {plugin}@{market}`:",
                "",
            ]
            lines += [
                f"- `{key}`: {option.get('description', option.get('title', ''))}" for key, option in settings.items()
            ]
            lines.append("")

    if manifest["marketplace"].get("docs"):
        lines += [
            f"See the [plugin install guide]({manifest['marketplace']['docs']}) for skill names, updates, and API keys.",
            "",
        ]
    return "\n".join(lines)


# --- rendering --------------------------------------------------------------


def _write_json(path: Path, payload: dict) -> None:
    """Write JSON with the trailing newline the end-of-file hook expects."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render(manifest: dict, root: Path, out_plugins: Path, out_marketplace: Path) -> None:
    """Render every plugin plus the marketplace catalog into the given output paths."""
    skills_root = root / "skills"
    tracked = tracked_paths(root)
    license_file = root / "LICENSE"
    icon_file = root / manifest["icon"] if manifest.get("icon") else None
    if icon_file is not None and not icon_file.is_file():
        raise RenderError(f"icon not found: {manifest['icon']}")
    entries = []

    for plugin, spec in manifest["plugins"].items():
        meta = _metadata(manifest, plugin, spec)
        plugin_dir = out_plugins / plugin
        for skill in sorted(spec["skills"]):
            copy_skill(skills_root / skill, plugin_dir / "skills" / skill, tracked)

        _write_json(plugin_dir / ".claude-plugin" / "plugin.json", claude_plugin_manifest(meta, spec))
        (plugin_dir / "README.md").write_text(plugin_readme(manifest, plugin, spec, skills_root), encoding="utf-8")
        if icon_file is not None:
            shutil.copyfile(icon_file, plugin_dir / ICON_PATH)
        if license_file.is_file():
            shutil.copy2(license_file, plugin_dir / "LICENSE")
        entries.append(marketplace_entry(meta, plugin))

    (out_plugins / "README.md").write_text(GENERATED_README, encoding="utf-8")

    market = manifest["marketplace"]
    catalog = {"name": market["name"], "owner": market["owner"]}
    if "description" in market:
        catalog["description"] = market["description"]
    catalog["plugins"] = entries
    _write_json(out_marketplace, catalog)


# --- drift check ------------------------------------------------------------


def snapshot(root: Path) -> dict[str, str]:
    """Describe a tree as path -> content digest or symlink target, for comparison."""
    if not root.exists():
        return {}
    found = {}
    for path in sorted(root.rglob("*")):
        key = str(path.relative_to(root))
        if path.is_symlink():
            found[key] = "link:" + os.readlink(path)
        elif path.is_file():
            found[key] = "file:" + hashlib.sha256(path.read_bytes()).hexdigest()
    return found


def _same_file(expected: Path, actual: Path) -> bool:
    """Compare two files by content, treating a missing file as different."""
    return actual.is_file() and expected.read_bytes() == actual.read_bytes()


def diff_report(expected: dict[str, str], actual: dict[str, str], label: str) -> list[str]:
    """List the paths where a rendered tree and the committed tree disagree."""
    lines = []
    lines += [f"  missing: {label}/{key}" for key in sorted(set(expected) - set(actual))]
    lines += [f"  unexpected: {label}/{key}" for key in sorted(set(actual) - set(expected))]
    lines += [f"  stale: {label}/{key}" for key in sorted(set(expected) & set(actual)) if expected[key] != actual[key]]
    return lines


def main(argv: list[str] | None = None) -> int:
    """Render the plugins, or report drift when called with --check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report drift instead of writing; exit 1 if any")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="repository root")
    args = parser.parse_args(argv)

    root: Path = args.root.resolve()
    plugins_dir = root / "plugins"
    marketplace_file = root / ".claude-plugin" / "marketplace.json"

    try:
        manifest = load_manifest(root / "plugins.yaml")
        validate_coverage(manifest, root / "skills")
        validate_dependencies(manifest)

        # Staged inside the repo so the final move is a rename on one filesystem,
        # and a failed render leaves the committed tree untouched.
        with tempfile.TemporaryDirectory(prefix=".render-plugins-", dir=root) as tmp:
            staged_plugins = Path(tmp) / "plugins"
            staged_marketplace = Path(tmp) / "marketplace.json"
            render(manifest, root, staged_plugins, staged_marketplace)

            if args.check:
                problems = diff_report(snapshot(staged_plugins), snapshot(plugins_dir), "plugins")
                if not _same_file(staged_marketplace, marketplace_file):
                    problems.append("  stale: .claude-plugin/marketplace.json")
                if problems:
                    print("plugins/ is out of date with plugins.yaml:", file=sys.stderr)
                    print("\n".join(problems), file=sys.stderr)
                    print("\nrun `just render-plugins` to update", file=sys.stderr)
                    return 1
                print(f"plugins/ is up to date ({len(manifest['plugins'])} plugins)")
                return 0

            if plugins_dir.exists():
                shutil.rmtree(plugins_dir)
            shutil.move(str(staged_plugins), str(plugins_dir))
            marketplace_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(staged_marketplace), str(marketplace_file))
    except RenderError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"rendered {len(manifest['plugins'])} plugins into {plugins_dir.relative_to(root)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
