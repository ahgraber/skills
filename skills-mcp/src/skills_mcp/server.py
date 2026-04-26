from __future__ import annotations

import argparse
import logging
import sys
from typing import Literal

from fastmcp import FastMCP
from fastmcp.server.transforms import ResourcesAsTools

from skills_mcp.discovery import RootSpec, discover_roots, parse_root_arg
from skills_mcp.provider import DedupSkillsDirectoryProvider

ExposeMode = Literal["resources", "tools", "both"]

_DESCRIPTION_CHAR_BUDGET = 240


def _format_skill_index(provider: DedupSkillsDirectoryProvider, expose: ExposeMode) -> str:
    """Compose the Tier-1 skill index that goes into the MCP `instructions` field.

    The index lists every resolved skill with its frontmatter description so the
    model can choose a skill without first calling list_resources / list_tools.
    """
    lines: list[str] = [
        "Aggregates agent skills from well-known locations (~/.claude/skills, "
        "~/.agents/skills, vendor-specific dirs). Duplicates are collapsed by "
        "symlink and content hash; true name collisions are exposed under "
        "namespaced URIs (e.g. skill://claude--foo).",
        "",
        "## URI scheme",
        "",
        "- `skill://{name}/SKILL.md` - main instruction body for the skill",
        "- `skill://{name}/_manifest` - JSON listing of files in the skill",
        "- `skill://{name}/{path}` - a supporting file inside the skill",
        "",
    ]
    if expose == "tools":
        lines.append("Access skills via the `read_resource` tool with a `skill://...` URI.")
    elif expose == "both":
        lines.append(
            "Access skills via MCP resources or via the `read_resource` tool (both are wired to the same backend)."
        )
    else:
        lines.append("Access skills via standard MCP resource calls.")
    lines.append("")

    skills = sorted(
        (p for p in provider.providers if hasattr(p, "skill_info")),
        key=lambda p: p.skill_info.name,
    )
    if not skills:
        lines.append("_No skills are currently loaded._")
        return "\n".join(lines)

    lines.append(f"## Available skills ({len(skills)})")
    lines.append("")
    for sp in skills:
        info = sp.skill_info
        desc = (info.description or "").strip().replace("\n", " ")
        if len(desc) > _DESCRIPTION_CHAR_BUDGET:
            desc = desc[: _DESCRIPTION_CHAR_BUDGET - 1].rstrip() + "…"
        lines.append(f"- **{info.name}** — {desc}" if desc else f"- **{info.name}**")
    return "\n".join(lines)


def build_server(
    *,
    extra_roots: list[RootSpec] | None = None,
    include_known: bool = True,
    include_env: bool = True,
    include_labels: list[str] | None = None,
    exclude_labels: list[str] | None = None,
    reload: bool = False,
    main_file_name: str = "SKILL.md",
    supporting_files: Literal["template", "resources"] = "template",
    expose: ExposeMode = "both",
) -> FastMCP:
    """Construct a FastMCP server pre-loaded with the dedup skills provider.

    Args:
        expose: 'resources' keeps the default MCP resource surface; 'tools' adds
            FastMCP's ResourcesAsTools transform so clients without resource
            support can use generic `list_resources` / `read_resource` tools;
            'both' exposes both surfaces.
    """
    roots = discover_roots(
        extra=extra_roots or (),
        include_known=include_known,
        include_env=include_env,
        include_labels=include_labels,
        exclude_labels=exclude_labels or (),
    )
    if not roots:
        logging.getLogger("skills_mcp").warning("No skills roots resolved - server will start with zero skills.")

    provider = DedupSkillsDirectoryProvider(
        roots=roots,
        reload=reload,
        main_file_name=main_file_name,
        supporting_files=supporting_files,
    )

    mcp = FastMCP(
        name="skills-mcp",
        instructions=_format_skill_index(provider, expose),
    )
    mcp.add_provider(provider)

    if expose in ("tools", "both"):
        # ResourcesAsTools registers `list_resources` and `read_resource` tools
        # that route through the server's middleware chain back to our provider,
        # so tools-only clients can still browse and read every skill resource.
        mcp.add_transform(ResourcesAsTools(mcp))

    return mcp


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="skills-mcp",
        description="Stdio MCP server that aggregates and deduplicates agent skills.",
    )
    p.add_argument(
        "--root",
        action="append",
        default=[],
        metavar="[LABEL=]PATH",
        help="Add a skills root (repeatable). Optional LABEL= prefix overrides the auto-derived namespace label.",
    )
    p.add_argument(
        "--no-vendor",
        action="store_true",
        help="Skip auto-discovery of well-known vendor skill directories.",
    )
    p.add_argument(
        "--no-env",
        action="store_true",
        help="Ignore the SKILLS_MCP_ROOTS environment variable.",
    )
    p.add_argument(
        "--include",
        action="append",
        default=[],
        metavar="LABEL",
        help="Restrict vendor discovery to these labels (repeatable). "
        "Labels: project, claude, agents, cursor, codex, gemini, copilot, opencode, goose.",
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=[],
        metavar="LABEL",
        help="Exclude these vendor labels from discovery (repeatable).",
    )
    p.add_argument(
        "--reload",
        action="store_true",
        help="Re-scan skill directories on every request (slower; useful while editing skills).",
    )
    p.add_argument(
        "--main-file",
        default="SKILL.md",
        metavar="NAME",
        help="Name of the main skill file (default: SKILL.md).",
    )
    p.add_argument(
        "--supporting-files",
        choices=("template", "resources"),
        default="template",
        help="How supporting files are exposed: 'template' (lazy via manifest) "
        "or 'resources' (each enumerated upfront). Default: template.",
    )
    p.add_argument(
        "--expose",
        choices=("resources", "tools", "both"),
        default="both",
        help="Surface to advertise skills on. 'both' (default) exposes the "
        "standard MCP resource API plus generic list_resources / read_resource "
        "tools for clients that lack resource support. 'resources' or 'tools' "
        "restrict to a single surface.",
    )
    p.add_argument(
        "--log-level",
        default="INFO",
        choices=("DEBUG", "INFO", "WARNING", "ERROR"),
        help="Logging level (default: INFO).",
    )
    return p


def main(argv: list[str] | None = None) -> None:
    """CLI entry point: parse args, build the server, and run it on stdio."""
    args = _build_parser().parse_args(argv)

    # FastMCP's stdio transport uses stdout for MCP framing - logs MUST go to stderr.
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stderr,
    )

    extra_roots = [parse_root_arg(r) for r in args.root]
    mcp = build_server(
        extra_roots=extra_roots,
        include_known=not args.no_vendor,
        include_env=not args.no_env,
        include_labels=args.include or None,
        exclude_labels=args.exclude,
        reload=args.reload,
        main_file_name=args.main_file,
        supporting_files=args.supporting_files,
        expose=args.expose,
    )
    mcp.run()  # stdio default
