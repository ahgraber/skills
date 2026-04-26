from __future__ import annotations

from pathlib import Path

from fastmcp import Client
import pytest
from skills_mcp.discovery import RootSpec
from skills_mcp.server import build_server


@pytest.fixture
def populated_root(tmp_path: Path, make_skill) -> RootSpec:
    make_skill(tmp_path, "alpha", body="Alpha body.\n")
    make_skill(tmp_path, "beta", body="Beta body.\n")
    return RootSpec("test", tmp_path)


def _build(populated_root: RootSpec, expose: str):
    return build_server(
        extra_roots=[populated_root],
        include_known=False,
        include_env=False,
        expose=expose,
    )


async def test_expose_resources_only_no_tools(populated_root: RootSpec):
    mcp = _build(populated_root, "resources")
    async with Client(mcp) as c:
        assert await c.list_tools() == []
        resources = await c.list_resources()
        assert {str(r.uri) for r in resources} >= {
            "skill://alpha/SKILL.md",
            "skill://beta/SKILL.md",
        }


async def test_default_expose_is_both(populated_root: RootSpec):
    mcp = build_server(
        extra_roots=[populated_root],
        include_known=False,
        include_env=False,
    )
    async with Client(mcp) as c:
        names = {t.name for t in await c.list_tools()}
        assert {"list_resources", "read_resource"} <= names
        resources = await c.list_resources()
        assert any(str(r.uri) == "skill://alpha/SKILL.md" for r in resources)


async def test_expose_tools_adds_resource_proxy_tools(populated_root: RootSpec):
    mcp = _build(populated_root, "tools")
    async with Client(mcp) as c:
        names = {t.name for t in await c.list_tools()}
        assert {"list_resources", "read_resource"} <= names

        result = await c.call_tool("read_resource", {"uri": "skill://alpha/SKILL.md"})
        text = result.content[0].text
        assert "Alpha body." in text


async def test_expose_both_keeps_resources_and_tools(populated_root: RootSpec):
    mcp = _build(populated_root, "both")
    async with Client(mcp) as c:
        tool_names = {t.name for t in await c.list_tools()}
        assert {"list_resources", "read_resource"} <= tool_names
        resources = await c.list_resources()
        assert any(str(r.uri) == "skill://alpha/SKILL.md" for r in resources)


async def test_instructions_carry_skill_index(populated_root: RootSpec):
    mcp = _build(populated_root, "tools")
    text = mcp.instructions or ""
    assert "alpha" in text and "beta" in text
    assert "skill://" in text
    assert "read_resource" in text
