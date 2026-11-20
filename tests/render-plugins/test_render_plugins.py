#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "pytest>=8.0",
#   "pyyaml>=6.0",
# ]
# ///
"""Tests for scripts/render_plugins.py, the plugin renderer."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import yaml

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts" / "render_plugins.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("render_plugins", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rp = _load_module()


# --- fixtures ---------------------------------------------------------------


def _skill(root: Path, name: str, body: str = "stub") -> Path:
    """Create a minimal skill directory."""
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(f"---\nname: {name}\n---\n\n{body}\n", encoding="utf-8")
    return skill


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    """A repo-shaped tree: two skills that share a reference, one that reaches outside skills/."""
    _skill(tmp_path, "alpha")
    (tmp_path / "skills" / "alpha" / "references").mkdir()
    (tmp_path / "skills" / "alpha" / "references" / "shared.md").write_text("shared\n", encoding="utf-8")

    _skill(tmp_path, "beta")
    (tmp_path / "skills" / "beta" / "references").mkdir()
    os.symlink("../../alpha/references/shared.md", tmp_path / "skills" / "beta" / "references" / "shared.md")

    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "tool.py").write_text("print('hi')\n", encoding="utf-8")
    _skill(tmp_path, "gamma")
    (tmp_path / "skills" / "gamma" / "scripts").mkdir()
    os.symlink("../../../scripts/tool.py", tmp_path / "skills" / "gamma" / "scripts" / "tool.py")

    (tmp_path / "LICENSE").write_text("license text\n", encoding="utf-8")
    return tmp_path


def _write_manifest(root: Path, plugins: dict, unbundled: list[str] | None = None) -> Path:
    """Write a plugins.yaml with the given plugins."""
    manifest = {
        "version": "1.2.3",
        "marketplace": {"name": "test-market", "owner": {"name": "tester"}},
        "defaults": {"license": "MIT"},
        "plugins": plugins,
    }
    if unbundled is not None:
        manifest["unbundled"] = unbundled
    path = root / "plugins.yaml"
    path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return path


def _render(root: Path) -> int:
    """Run the renderer against a workspace root."""
    return rp.main(["--root", str(root)])


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


ALL = {"one": {"skills": ["alpha", "beta", "gamma"]}}


# --- coverage validation ----------------------------------------------------


def test_every_skill_must_be_placed(workspace: Path):
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta"]}})
    with pytest.raises(rp.RenderError, match="gamma"):
        rp.validate_coverage(rp.load_manifest(workspace / "plugins.yaml"), workspace / "skills")


def test_unbundled_satisfies_coverage(workspace: Path):
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta"]}}, unbundled=["gamma"])
    rp.validate_coverage(rp.load_manifest(workspace / "plugins.yaml"), workspace / "skills")


def test_skill_in_two_plugins_is_rejected(workspace: Path):
    """Plugin skills never dedupe, so a shared skill would be listed twice once both are installed."""
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta"]}, "two": {"skills": ["alpha", "gamma"]}})
    with pytest.raises(rp.RenderError, match="more than one plugin"):
        rp.validate_coverage(rp.load_manifest(workspace / "plugins.yaml"), workspace / "skills")


def test_unknown_skill_is_rejected(workspace: Path):
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta", "gamma", "nope"]}})
    with pytest.raises(rp.RenderError, match="unknown skill 'nope'"):
        rp.validate_coverage(rp.load_manifest(workspace / "plugins.yaml"), workspace / "skills")


def test_skill_both_bundled_and_unbundled_is_rejected(workspace: Path):
    _write_manifest(workspace, ALL, unbundled=["gamma"])
    with pytest.raises(rp.RenderError, match="'unbundled'"):
        rp.validate_coverage(rp.load_manifest(workspace / "plugins.yaml"), workspace / "skills")


def test_empty_plugin_is_rejected(workspace: Path):
    _write_manifest(workspace, {**ALL, "two": {"skills": []}})
    with pytest.raises(rp.RenderError, match="lists no skills"):
        rp.validate_coverage(rp.load_manifest(workspace / "plugins.yaml"), workspace / "skills")


# --- dependencies -----------------------------------------------------------


def test_dependency_is_written_to_the_claude_manifest(workspace: Path):
    _write_manifest(
        workspace, {"base": {"skills": ["alpha"]}, "one": {"skills": ["beta", "gamma"], "dependencies": ["base"]}}
    )
    assert _render(workspace) == 0

    assert _read(workspace / "plugins" / "one" / ".claude-plugin" / "plugin.json")["dependencies"] == ["base"]
    assert "dependencies" not in _read(workspace / "plugins" / "base" / ".claude-plugin" / "plugin.json")


def test_dependency_on_an_unknown_plugin_is_reported(workspace: Path, capsys):
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta", "gamma"], "dependencies": ["ghost"]}})
    assert _render(workspace) == 1
    assert "unknown plugin 'ghost'" in capsys.readouterr().err


def test_dependency_on_itself_is_reported(workspace: Path, capsys):
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta", "gamma"], "dependencies": ["one"]}})
    assert _render(workspace) == 1
    assert "depends on itself" in capsys.readouterr().err


# --- symlink policy ---------------------------------------------------------


@pytest.mark.parametrize(
    ("relative", "content"),
    [
        # A link to another skill in the same plugin.
        ("beta/references/shared.md", "shared\n"),
        # A link out of skills/ to a repo-root script.
        ("gamma/scripts/tool.py", "print('hi')\n"),
    ],
)
def test_symlink_is_copied_as_its_content(workspace: Path, relative: str, content: str):
    """Codex drops symlinks when it caches a plugin, so each one must ship as a real file."""
    _write_manifest(workspace, ALL)
    assert _render(workspace) == 0

    copied = workspace / "plugins" / "one" / "skills" / relative
    assert not copied.is_symlink()
    assert copied.read_text(encoding="utf-8") == content


def test_rendered_tree_has_no_symlinks(workspace: Path):
    _write_manifest(workspace, {"one": {"skills": ["beta", "gamma"]}, "two": {"skills": ["alpha"]}})
    assert _render(workspace) == 0
    rendered = list((workspace / "plugins").rglob("*"))
    assert rendered
    assert [path for path in rendered if path.is_symlink()] == []


def test_build_droppings_are_not_copied(workspace: Path):
    """__pycache__ and friends are untracked, so copying them would make --check machine-dependent."""
    cache = workspace / "skills" / "alpha" / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    (cache / "alpha.cpython-313.pyc").write_bytes(b"\x00")
    (workspace / "skills" / "alpha" / ".DS_Store").write_bytes(b"\x00")

    _write_manifest(workspace, ALL)
    assert _render(workspace) == 0

    rendered = workspace / "plugins" / "one" / "skills" / "alpha"
    assert not (rendered / "scripts" / "__pycache__").exists()
    assert not (rendered / ".DS_Store").exists()


def test_untracked_files_are_not_copied(workspace: Path):
    """A plugin mirrors what ships, so an untracked file beside a skill cannot reach it."""
    subprocess.run(["git", "init", "-q"], cwd=workspace, check=True)
    (workspace / ".gitignore").write_text("*.pdf\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=workspace, check=True)

    (workspace / "skills" / "alpha" / "references" / "manual.pdf").write_bytes(b"%PDF-1.4\n")
    (workspace / "skills" / "alpha" / "references" / "scratch.md").write_text("not added\n", encoding="utf-8")

    _write_manifest(workspace, ALL)
    assert _render(workspace) == 0

    rendered = workspace / "plugins" / "one" / "skills" / "alpha" / "references"
    assert (rendered / "shared.md").is_file()
    assert not (rendered / "manual.pdf").exists()
    assert not (rendered / "scratch.md").exists()


def test_untracked_filter_is_skipped_outside_a_checkout(workspace: Path):
    """Rendering still works where git cannot answer, so the tests and a tarball export both run."""
    assert rp.tracked_paths(workspace) is None
    _write_manifest(workspace, ALL)
    assert _render(workspace) == 0
    assert (workspace / "plugins" / "one" / "skills" / "alpha" / "SKILL.md").is_file()


def test_broken_symlink_is_reported(workspace: Path, capsys):
    os.symlink("../../nowhere.md", workspace / "skills" / "alpha" / "references" / "dangling.md")
    _write_manifest(workspace, ALL)
    assert _render(workspace) == 1
    assert "broken symlink" in capsys.readouterr().err


# --- manifests --------------------------------------------------------------


MCP_PLUGIN = {
    "one": {
        "description": "d",
        "skills": ["alpha", "beta", "gamma"],
        "mcp": {
            "remote": {"type": "streamable-http", "url": "https://example.test/mcp"},
            "local": {"type": "stdio", "command": "./bin/x", "args": ["--data", "${PLUGIN_DATA}/x"]},
        },
        "claude": {
            "userConfig": {"token": {"type": "string", "title": "T", "description": "D", "sensitive": True}},
            "mcpServers": {"remote": {"headers": {"Authorization": "Bearer ${user_config.token}"}}},
        },
    }
}


def test_claude_manifest_carries_mcp_and_user_config(workspace: Path):
    _write_manifest(workspace, MCP_PLUGIN)
    assert _render(workspace) == 0

    manifest = _read(workspace / "plugins" / "one" / ".claude-plugin" / "plugin.json")
    assert manifest["name"] == "one"
    assert manifest["version"] == "1.2.3"
    assert manifest["userConfig"]["token"]["sensitive"] is True
    assert manifest["mcpServers"]["remote"]["headers"]["Authorization"] == "Bearer ${user_config.token}"


def test_transport_and_placeholders_are_translated_for_claude(workspace: Path):
    _write_manifest(workspace, MCP_PLUGIN)
    assert _render(workspace) == 0

    servers = _read(workspace / "plugins" / "one" / ".claude-plugin" / "plugin.json")["mcpServers"]
    assert servers["remote"]["type"] == "http"
    assert servers["local"]["type"] == "stdio"
    assert servers["local"]["args"] == ["--data", "${CLAUDE_PLUGIN_DATA}/x"]


def test_unsupported_transport_is_reported(workspace: Path, capsys):
    _write_manifest(
        workspace, {"one": {"skills": ["alpha", "beta", "gamma"], "mcp": {"x": {"type": "carrier-pigeon"}}}}
    )
    assert _render(workspace) == 1
    assert "unsupported type" in capsys.readouterr().err


def test_marketplace_entry_points_at_the_plugin_directory(workspace: Path):
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta"]}, "two": {"skills": ["gamma"]}})
    assert _render(workspace) == 0

    catalog = _read(workspace / ".claude-plugin" / "marketplace.json")
    assert catalog["name"] == "test-market"
    assert [entry["source"] for entry in catalog["plugins"]] == ["./plugins/one", "./plugins/two"]
    assert {entry["version"] for entry in catalog["plugins"]} == {"1.2.3"}


def test_plugin_without_mcp_has_no_mcp_servers(workspace: Path):
    _write_manifest(workspace, ALL)
    assert _render(workspace) == 0

    plugin = workspace / "plugins" / "one"
    assert "mcpServers" not in _read(plugin / ".claude-plugin" / "plugin.json")
    assert not (plugin / ".mcp.json").exists()


# --- README and icon --------------------------------------------------------


def _describe(root: Path, name: str, description: str) -> None:
    (root / "skills" / name / "SKILL.md").write_text(
        yaml.safe_dump({"name": name, "description": description}).join(["---\n", "---\n\nstub\n"]), encoding="utf-8"
    )


def test_readme_lists_each_skill_by_its_first_sentence(workspace: Path):
    _describe(workspace, "alpha", "Use when testing alpha (e.g. a unit test). Triggers: 'alpha', 'first'.")
    _write_manifest(workspace, ALL)
    assert _render(workspace) == 0

    readme = (workspace / "plugins" / "one" / "README.md").read_text(encoding="utf-8")
    assert readme.startswith("# one\n")
    assert "- `alpha`: Use when testing alpha (e.g. a unit test).\n" in readme
    assert "Triggers" not in readme
    assert "- `beta`:" in readme


def test_readme_installs_dependencies_where_the_harness_does_not(workspace: Path):
    _write_manifest(
        workspace, {"base": {"skills": ["alpha"]}, "one": {"skills": ["beta", "gamma"], "dependencies": ["base"]}}
    )
    assert _render(workspace) == 0

    readme = (workspace / "plugins" / "one" / "README.md").read_text(encoding="utf-8")
    assert "claude plugin install base@" not in readme
    assert "codex plugin add base@test-market\ncodex plugin add one@test-market" in readme
    assert "copilot plugin install base@test-market\ncopilot plugin install one@test-market" in readme
    assert "dependencies" not in (workspace / "plugins" / "base" / "README.md").read_text(encoding="utf-8")


def test_readme_describes_mcp_servers_and_settings(workspace: Path):
    _write_manifest(workspace, MCP_PLUGIN)
    assert _render(workspace) == 0

    readme = (workspace / "plugins" / "one" / "README.md").read_text(encoding="utf-8")
    assert "- `remote`: https://example.test/mcp" in readme
    assert "- `token`: D" in readme


def test_privacy_policy_reaches_manifest_and_readme(workspace: Path):
    url = "https://example.test/privacy"
    _write_manifest(workspace, {"one": {**MCP_PLUGIN["one"], "privacy": url}})
    assert _render(workspace) == 0

    plugin_dir = workspace / "plugins" / "one"
    manifest = json.loads((plugin_dir / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    assert manifest["privacyPolicyUrl"] == url
    assert url in (plugin_dir / "README.md").read_text(encoding="utf-8")


def test_icon_is_copied_into_each_plugin(workspace: Path):
    (workspace / "assets").mkdir()
    (workspace / "assets" / "icon.png").write_bytes(b"\x89PNG fake")
    path = _write_manifest(workspace, {"one": {"skills": ["alpha"]}, "two": {"skills": ["beta", "gamma"]}})
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    path.write_text(yaml.safe_dump({**manifest, "icon": "assets/icon.png"}), encoding="utf-8")
    assert _render(workspace) == 0

    for plugin in ("one", "two"):
        assert (workspace / "plugins" / plugin / ".claude-plugin" / "icon.png").read_bytes() == b"\x89PNG fake"


def test_missing_icon_is_reported(workspace: Path, capsys):
    path = _write_manifest(workspace, ALL)
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    path.write_text(yaml.safe_dump({**manifest, "icon": "assets/nope.png"}), encoding="utf-8")
    assert _render(workspace) == 1
    assert "icon not found: assets/nope.png" in capsys.readouterr().err


# --- drift check ------------------------------------------------------------


def test_check_passes_after_render_and_fails_after_edit(workspace: Path, capsys):
    _write_manifest(workspace, ALL)
    assert _render(workspace) == 0
    capsys.readouterr()

    assert rp.main(["--root", str(workspace), "--check"]) == 0

    (workspace / "plugins" / "one" / "skills" / "alpha" / "SKILL.md").write_text("tampered\n", encoding="utf-8")
    assert rp.main(["--root", str(workspace), "--check"]) == 1
    assert "stale" in capsys.readouterr().err


def test_check_detects_a_removed_plugin(workspace: Path, capsys):
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta"]}, "two": {"skills": ["gamma"]}})
    assert _render(workspace) == 0
    _write_manifest(workspace, {"one": {"skills": ["alpha", "beta"]}}, unbundled=["gamma"])
    capsys.readouterr()

    assert rp.main(["--root", str(workspace), "--check"]) == 1
    assert "unexpected: plugins/two" in capsys.readouterr().err


def test_render_is_idempotent(workspace: Path):
    _write_manifest(workspace, MCP_PLUGIN)
    assert _render(workspace) == 0
    first = rp.snapshot(workspace / "plugins")
    assert _render(workspace) == 0
    assert rp.snapshot(workspace / "plugins") == first


# --- the repository's own manifest ------------------------------------------


def test_repo_manifest_places_every_skill():
    """A skill added to skills/ without a home in plugins.yaml fails the build."""
    rp.validate_coverage(rp.load_manifest(REPO / "plugins.yaml"), REPO / "skills")


def test_repo_manifest_dependencies_resolve():
    rp.validate_dependencies(rp.load_manifest(REPO / "plugins.yaml"))


if __name__ == "__main__":
    _here = str(Path(__file__).resolve().parent)
    raise SystemExit(
        pytest.main(
            [str(Path(__file__).resolve()), "-v", "-p", "no:cacheprovider", "--rootdir", _here, "--confcutdir", _here]
        )
    )
