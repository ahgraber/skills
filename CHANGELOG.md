# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- `subagent-patterns` — a dispatch delegates labor, not accountability: briefs must carry the
  positive standard (a worked exemplar and rubric for quality-bar work like writing, design, or
  naming), not just constraints, or the worker satisfices to the smallest change that clears the
  bans; tacit-standard work (taste, voice, register, craft) stays inline.

## [1.1.0] - 2026-07-11

### Added

- `subagent-patterns` skill — a decision framework for subagent-supported development: resolve each
  dispatch along five axes (whether to dispatch, model tier, role, isolation, wiring) rather
  than picking a named pattern, with worked big:little (orchestrator) and little:big (oracle)
  presets, an archetype-decode step, a file-handoff dispatch discipline, and a per-task review
  loop. In-harness by design; defers to purpose-built skills (`code-review`, `sdd-verify`, and
  others) that own their own subagent-dispatch rules.

## [1.0.0] - 2026-07-10

First stable release. From here: breaking changes bump MAJOR, new skills/features bump
MINOR, fixes bump PATCH.

### Breaking Changes

- Removed the `spec-kit` skill family (`spec-kit`, `spec-kit-analyze`,
  `spec-kit-checklist`, `spec-kit-clarify`, `spec-kit-constitution`,
  `spec-kit-implement`, `spec-kit-plan`, `spec-kit-reconcile`, `spec-kit-specify`,
  `spec-kit-tasks`) — use the `sdd` skill suite instead.

## [0.16.0] - 2026-07-10

### Added

- `explain-diff` skill — turns a code change (diff, branch, commit, staged changes, or
  PR) into a self-contained, interactive HTML or Markdown learning artifact with a
  self-check quiz, grounded in learning-science principles.

## [0.15.0] - 2026-06-28

### Added

- `deep-research` skill for multi-round, verified web research.

### Changed

- `good-prose` now requires headings and sentences to carry information.

## [0.14.0] - 2026-06-25

### Added

- `security-scan` skillset (OpenAI-inspired), plus companion `security-deep-scan`,
  `security-fix-finding`, and `security-triage-finding` skills.
- Repo-utility scripts for OCR (`docling-ocr`) and page-markdown extraction
  (`download-page-markdown`).

### Changed

- `code-review` — pre-baked review packet, shared with `simplify`.
- Documented portability and agent-native script guidance for `optimize-skills` and
  `shell-scripts`.
- Clarified SDD spec-format requirement-modification rules, scenario naming, and
  `.verify/` directory usage.

### Fixed

- `visual-brainstorming` — fixed a server crash, hang, and unsafe file reads.
- `spec-kit` — return a non-zero exit code when a prefix matches multiple spec
  directories.

## [0.13.0] - 2026-06-17

### Added

- `strudel` skill for live-coding music patterns.
- `synthesize` skill for spine-led synthesis of source material.
- `editorial-review` skill for sparring-partner-style draft feedback.
- `interactive-notebook-demo` skill for feature-demo notebooks.
- North-star and user-story value layer in `sdd`.

### Changed

- Clarified `skills-mcp` installation instructions.

### Fixed

- `sdd` — guarded MODIFIED deltas from silently dropping baseline scenarios; added
  scope checks for unspecified changes.

## [0.12.0] - 2026-05-13

### Added

- `writing-tests` skill; `python-testing` gained test-double and portfolio-strategy
  guidance.

### Changed

- Unified and named `commit-message` body-discipline rules under a "cold-reader" test.
- Clarified README usage and contribution guidance.

### Fixed

- `sdd` — pinned the `SPECS_ROOT` contract and pointer-file semantics, ordered
  capability/task lists by build dependency, improved verification granularity, and
  supported multi-spec targets in monorepos.
- `proof` — tightened instructions to prefer direct file edits.

## [0.11.0] - 2026-05-03

### Added

- `alt-text` skill for describing images, charts, and diagrams.
- `debugging` skill.
- `changelog` skill for drafting `CHANGELOG.md` updates.

### Fixed

- Behavioral refinements across `api-design` (Hyrum's Law), `simplify`
  (behavior-preserving guards), `brainstorming` (additional lenses), `securing-code`
  (supply-chain checks), `python-testing`, and `code-review`.

## [0.10.0] - 2026-04-30

### Breaking Changes

- `skills-mcp` — sanitized the skill index and removed over-engineered parameters from
  its interface; callers passing the removed params must update calls.

### Added

- `skills-mcp`, a stdio MCP server that aggregates and deduplicates agent skills from
  vendor locations.
- SDD discovery script for resolving `SPECS_ROOT` candidates.

### Changed

- Hardened `skills-mcp`'s instructions surface and simplified its internals.
- `sdd-derive` — now uses subagent fan-out with reconciliation.

### Fixed

- Clarified task-referencing guidelines in `sdd-apply`.
- `sdd verify` now runs the full test suite instead of a worked subset.
- Reinforced the no-ephemeral-references rule across `sdd-apply` and `commit-message`.

## [0.9.0] - 2026-04-23

### Added

- `securing-code` skill based on OWASP Top 10 and secure-coding heuristics.
- `brainstorming` and `visual-brainstorming` skills.

### Changed

- Reframed `sdd` specs as outcome-contracts rather than procedures.
- `code-review` — added parallel-subagent review support.

### Fixed

- `commit-message` — added an override branch for edge-case workflows.

## [0.8.0] - 2026-04-12

### Added

- `receiving-feedback` skill for processing code review or doc-revision feedback.
- `simplify` skill for reuse/quality/efficiency passes on changed code.
- Pre-diagnostic git commands in `code-review` to surface hotspots before review.
- Testing-matrix references (nox, free-threaded Python) in `python-testing`.

### Changed

- All skills now announce invocation by name.
- Documented using skills with Claude Code on the web.

### Fixed

- Increased `receiving-feedback` invocation frequency by requiring its use.

## [0.7.0] - 2026-04-04

### Added

- `sdd` (spec-driven development) skill suite, including schema-conformance lifecycle
  checks.
- `api-design` skill with references for REST/GraphQL, pagination, URI design, and
  versioning.

### Changed

- `code-review` — added graph-aided triage tools.

### Fixed

- SDD specs-root resolution made more flexible, with an escape hatch for complex repo
  layouts; added warnings for missing schema config and stale artifacts; standardized
  on `.specs` as the schema config path; resolved unspecified derive/translate behavior
  for greenfield projects.
- Corrected stale RFC references and improved clarity in `api-design` docs.

## [0.6.0] - 2026-03-10

### Added

- `shell-scripts` skill covering shebang selection, quoting, and ShellCheck-guided
  fixes.
- `proof` skill for proofreading and light copy edits.
- AI writing tropes reference document (used by prose-related skills).

### Fixed

- Quoted skill frontmatter descriptions where required to keep YAML valid.

## [0.5.0] - 2026-02-08

### Added

- `spec-kit` skill suite with routed sub-skills, templates, and workflow tooling.
- `spec-kit-reconcile` skill for resolving spec drift.

## [0.4.0] - 2026-02-08

### Breaking Changes

- Renamed the `ai-skills` skill to `optimize-skills` — update any direct invocations
  (`/ai-skills` → `/optimize-skills`) and installed-skill references.

### Fixed

- Re-ran optimize-skills' self-optimization pass on its own definition.
- Removed the trigger-tests section from optimize-skills' generated output.

## [0.3.0] - 2026-02-07

### Added

- `mcp-research` skill for sourcing current technical documentation.
- `code-review` skill with issue template and best-practices references.
- `handoff` skill and template for transferring work between sessions.
- `commit-message` skill for drafting Conventional Commit messages.

### Changed

- Moved skill templates into `assets/` and refreshed README installation/usage
  instructions.

## [0.2.0] - 2026-02-06

### Added

- Python skill router plus ten focused sub-skills: concurrency & performance, data &
  state, design & modularity, errors & reliability, integrations & resilience,
  notebooks/async, runtime operations, testing, types & contracts, and workflow &
  delivery.

### Changed

- Tightened Python skill descriptions and consolidated scope/invocation guidance
  across the suite.

## [0.1.0] - 2026-02-04

### Added

- Initial skill collection and repository scaffold, with installation instructions for
  the `skills.sh` CLI (`npx skills add`).

[0.1.0]: https://github.com/ahgraber/skills/releases/tag/v0.1.0
[0.10.0]: https://github.com/ahgraber/skills/compare/v0.9.0...v0.10.0
[0.11.0]: https://github.com/ahgraber/skills/compare/v0.10.0...v0.11.0
[0.12.0]: https://github.com/ahgraber/skills/compare/v0.11.0...v0.12.0
[0.13.0]: https://github.com/ahgraber/skills/compare/v0.12.0...v0.13.0
[0.14.0]: https://github.com/ahgraber/skills/compare/v0.13.0...v0.14.0
[0.15.0]: https://github.com/ahgraber/skills/compare/v0.14.0...v0.15.0
[0.16.0]: https://github.com/ahgraber/skills/compare/v0.15.0...v0.16.0
[0.2.0]: https://github.com/ahgraber/skills/compare/v0.1.0...v0.2.0
[0.3.0]: https://github.com/ahgraber/skills/compare/v0.2.0...v0.3.0
[0.4.0]: https://github.com/ahgraber/skills/compare/v0.3.0...v0.4.0
[0.5.0]: https://github.com/ahgraber/skills/compare/v0.4.0...v0.5.0
[0.6.0]: https://github.com/ahgraber/skills/compare/v0.5.0...v0.6.0
[0.7.0]: https://github.com/ahgraber/skills/compare/v0.6.0...v0.7.0
[0.8.0]: https://github.com/ahgraber/skills/compare/v0.7.0...v0.8.0
[0.9.0]: https://github.com/ahgraber/skills/compare/v0.8.0...v0.9.0
[1.0.0]: https://github.com/ahgraber/skills/compare/v0.16.0...v1.0.0
[1.1.0]: https://github.com/ahgraber/skills/compare/v1.0.0...v1.1.0
[unreleased]: https://github.com/ahgraber/skills/compare/v1.1.0...HEAD
