# Changelog

All notable changes to the `skills-mcp` package are documented in this file.
This changelog covers `skills-mcp` **only**; the agent-skills collection is versioned separately in [../CHANGELOG.md](../CHANGELOG.md).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this package adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
Releases are cut with [uv-ship](https://floraths.github.io/uv-ship/) — see [RELEASING.md](RELEASING.md).

## [Unreleased]

## [0.2.0] - 2026-08-20

### Changed

- Move to FastMCP 4 (`fastmcp>=4.0.0b3,<5`).
  The server now negotiates a protocol era per connection: clients on MCP's sessionless `2026-07-28` protocol and clients on the `2025-11-25` handshake era both reach the same skills, from one server.
  FastMCP 4 is still a prerelease, so an install resolves to a beta; pin `skills-mcp` itself if that is not acceptable.

## [0.1.0] - 2026-07-12

### Added

- Stdio MCP server that aggregates agent skills from well-known vendor roots
  (`~/.claude/skills`, `~/.agents/skills`, `~/.cursor/skills`, …) and exposes each as
  MCP resources via FastMCP's `SkillsDirectoryProvider`.
- Dedup pipeline on top of FastMCP scanning: symlink/inode collapse, content-hash
  collapse, and namespaced handling of same-name / different-content collisions.
- Discovery controls — `--root` (with optional `LABEL=PATH`), `SKILLS_MCP_ROOTS`,
  `--include` / `--exclude`, and `--no-vendor` / `--no-env`.
- Progressive disclosure across three tiers: a compact skill index in the MCP
  `instructions` field, `SKILL.md` on demand, and `_manifest` plus supporting files.
- Tools-only surface (`--expose`) for clients that do not implement the resources
  protocol, exposing `list_resources` and `read_resource`.

[0.1.0]: https://github.com/ahgraber/skills/releases/tag/skills-mcp-v0.1.0
[0.2.0]: https://github.com/ahgraber/skills/compare/skills-mcp-v0.1.0...skills-mcp-v0.2.0
[unreleased]: https://github.com/ahgraber/skills/compare/skills-mcp-v0.2.0...HEAD
