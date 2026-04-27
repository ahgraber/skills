from __future__ import annotations

import argparse
import logging
import re
import sys
from typing import Literal

from fastmcp import FastMCP
from fastmcp.server.transforms import ResourcesAsTools

from skills_mcp.discovery import RootSpec, discover_roots, parse_root_arg
from skills_mcp.provider import DedupSkillsDirectoryProvider

logger = logging.getLogger("skills_mcp.server")

ExposeMode = Literal["resources", "tools", "both"]

_DESCRIPTION_CHAR_BUDGET = 240
_SKILL_NAME_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9 ._-]{0,63}$")
_NAMESPACE_SEP = "--"

_USING_SKILLS = """\
If you have not yet used the `skills__list_resources` tool you MUST use it immediately \
so you're aware of available skills. Skills provide prepackaged knowledge and workflows \
that the user wants you to have available.

## Using Skills

Skills are on-demand specialized workflows available via the `Skill` tool.
They are curated to guide _how_ you approach specific task types.

### The Rule

**Before any response or action, scan the available skills list `skills__list_resources` \
provides and invoke every plausibly relevant skill.**

- If the skill's description shares any concept with the task at hand — the user's current \
request understood in the full context of the conversation — it is plausibly relevant.
- Err toward invoking — the cost is near zero; skipping means missing established workflows.
  If unsure whether a skill applies, invoke it; do not require a perfect match.
- Re-invoke skills when the task changes within a conversation.
  Prior invocations apply to prior tasks.
- Skill invocation must precede all other cognitive work on the task.
  Read the request to understand what is being asked, then immediately scan and invoke \
— before analyzing the problem, forming an approach, or reasoning about implementation.
- Do not explore the codebase, gather context, or ask clarifying questions before checking \
skills — skills often define how to do those things.

#### Limited Exceptions

Skip skill invocation ONLY when:

1. You are a narrowly scoped subagent whose launch instructions already define your workflow.
2. No skill is plausibly relevant after a good-faith scan.
   List the 2-3 closest candidate skills and why each was ruled out.
3. The skill mechanism is unavailable or broken.
   State this explicitly.

### Execution

1. Read the user request.
2. Scan the skills list (shown in system reminders) for matching names and trigger descriptions.
3. Invoke every plausibly relevant skill via `Skill` (e.g., `skill: "commit-message"`).
   The full content loads into context.
4. Follow the loaded instructions.
   If the skill includes a checklist, create TodoWrite items for each step.
5. Announce which skill you are using and why \
(e.g., "Using `python-testing` to write these test cases.").

### Instruction priority

1. Highest priority: **User instructions** always take precedence, even over skill guidance.
2. **Skills** guide default behavior via specialized knowledge.
3. **Public directives** (CLAUDE.md, AGENTS.md) and system defaults are lowest priority.

User instructions define _what_ to do.
Skills define _how_.
A user instruction is not permission to skip the skill check — always scan and invoke first, \
then follow user intent within the loaded workflow.
Inferred urgency or simplicity is not an explicit user instruction; only skip skill steps \
when the user directly and specifically tells you to skip them.

### Ordering

When multiple skills apply, invoke in this order:

1. **Process skills** (brainstorming, code-review, receiving-feedback) — shape your approach.
2. **Implementation skills** (python-\\*, api-design, shell-scripts) — guide execution details.

### Skill types

- **Rigid**: the skill contains a numbered sequential workflow or checklist.
  Follow each step in order.
  Do not skip, reorder, or abbreviate.
- **Flexible**: the skill provides principles, heuristics, or reference routing.
  Adapt the guidance to the specific context.

When ambiguous, treat the skill as rigid."""


def _format_skill_index(provider: DedupSkillsDirectoryProvider, expose: ExposeMode) -> str:
    """Compose the Tier-1 skill index that goes into the MCP `instructions` field.

    The index lists every resolved skill with its frontmatter description so the
    model can choose a skill without first calling list_resources / list_tools.
    """
    lines: list[str] = [
        _USING_SKILLS,
        "",
        "---",
        "",
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
        name = (info.name or "").replace("**", "")
        if not _SKILL_NAME_RE.fullmatch(name) or _NAMESPACE_SEP in name:
            logger.warning("Omitting skill from index: name %r failed validation", info.name)
            continue
        desc = (info.description or "").strip().replace("\n", " ").replace("**", "")
        if len(desc) > _DESCRIPTION_CHAR_BUDGET:
            desc = desc[: _DESCRIPTION_CHAR_BUDGET - 1].rstrip() + "…"
        lines.append(f"- **{name}** — {desc}" if desc else f"- **{name}**")

    lines.append("")
    lines.append(
        "_This index reflects the skill set at server startup. "
        "Under `--reload`, use `list_resources` for the current set._"
    )
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

    Note: When no roots resolve (e.g. `--no-vendor --no-env` with no `--root`),
    the provider falls back to scanning the current working directory. Pair
    `--no-vendor` with at least one `--root` to restrict discovery explicitly.
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
