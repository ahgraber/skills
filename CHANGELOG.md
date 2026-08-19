# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Breaking Changes

- Remove `explain-diff`, `mermaid`, and `visual-brainstorming`; their jobs move into the new skills below. Migrate installs: "explain this diff/PR" asks now trigger `teach-me` (same phrases; artifacts default to `.teach/` instead of `.explain/`); the Mermaid validate/render scripts ship inside `show-me` (`skills/show-me/scripts/`) and now render on `uv` alone, so an `mmdc` (Mermaid CLI), Node, or Chromium install kept only for them can go — their `--install-chromium` flag goes with it; the browser-based visual companion is `show-me`'s consent-gated session (`references/visual-session.md`).
- Removed the routed `python-*` sub-skill family (`python-concurrency-performance`, `python-data-state`, `python-design-modularity`, `python-errors-reliability`, `python-integrations-resilience`, `python-runtime-operations`, `python-testing`, `python-types-contracts`, `python-workflow-delivery`) — install the reworked `python` skill instead; `python-notebooks-async` remains for notebook event-loop work. Free-threaded testing guidance drops to git history until a project targets free-threaded builds.

### Added

- `show-me` — one skill for "I need to see this": pseudocode, call/component/file trees, Mermaid, sketch-level diffs, focused HTML, and charts of the data at hand, plus a consent-gated interactive browser session for design discussions. Visuals are ephemeral by default and saved only on request; dashboards and other durable deliverables are out of scope. Mermaid diagrams can be parse-checked and written to SVG/PNG/PDF entirely offline — `render_mermaid.py` takes its format from the output extension and accepts `--background` and `--scale`.
- `teach-me` — turn any subject — a historical period, music theory, a legal concept, a library, a code change — into a sized lesson: light in-chat by default, up to a saved, dated artifact with an interactive quiz. Lessons are grounded in real sources, never coin terminology, and accrete in `.teach/` into a curriculum across invocations.
- `grill-me` — an elicitative interview in question rounds that draws out the user's decisions, unstated opinions, and silent assumptions until alignment is confirmed. Recommendations are placed or withheld per question so the user is not led; the settled understanding carries forward via `handoff` on request.

### Changed

- `brainstorming` — the description now advertises its adversarial lenses for stress-testing a plan already on the table, and a new Seams section draws `show-me` visuals inline and offers `grill-me` when the user holds something to elicit rather than shape.
- `handoff` — accepting another skill's offer to save now counts as the file request; the skill writes the file without asking again.
- `code-review` — no longer triggers for building understanding of a change; those asks route to `teach-me`.
- `receiving-feedback` — triggers on any feedback that evaluates an artifact the agent produced or is responsible for, not only review feedback.
- `python` — reworked from a router into one house-style audit skill: a ruff pass under the project's own lint configuration, plus a judgment sweep for defaults no linter can check. It now fires when a change is about to be called done or on any review/audit request, reporting findings instead of imposing rules while writing, and local project policy outranks every house default.
- `python` — the supply-chain audit scripts now audit the project they are invoked from: the workspace root resolves from the working directory rather than the scripts' install location, and `uv audit` support is probed rather than assumed, so a uv build too old to audit falls through to pip-audit instead of failing with the dependencies unaudited.
- `writing-tests` — gains Python-specific testing practice (mocking, pytest, async, dependency audits) as a reference shared from `skills/python`.
- `interactive-notebook-demo` — gains the notebook event-loop reference shared from `python-notebooks-async`.
- Fast-moving references (ruff coverage, the nox matrix, notebook async) now open with a `Last verified:` date naming what to re-check.

### Fixed

- `sdd-apply` and `sdd-translate` — ship the `references/sdd-change-formats.md` file both skills tell the reader to consult; following their task-ordering and change-directory steps previously landed on a file that was never installed with the skill.

## [2.4.0] - 2026-08-17

### Changed

- `handoff` — record session evidence, never invent continuation. The skill now serves conversational transfers (ideation, research, writing) as well as repository work; repo state and the Changes Made and Validation sections are conditional. Every statement must trace to the user's words, the session's actions, or an artifact, and repository claims are verified against the working tree rather than conversation memory. Next Steps becomes Continuation and carries only user-given direction or the remainder of requested work — when none was established the author asks, and when none is given the section is omitted. A new References section passes along consulted sources with a note on why the recipient needs each.

## [2.3.2] - 2026-08-16

### Changed

- `simplify` — a pass now runs in one of two modes, and the user names it at the gate: **audit** reports findings and changes nothing, **fix** applies the edits whose behavior preservation is verifiable. The mode is never inferred from phrasing and never switches mid-pass, so an audit that turns up an obvious fix still edits nothing. Both modes find, tier, and prove removals identically; the tier on an audit finding tells the reader which ones a later fix pass takes without asking. The ledger records the mode, and an audit ledger reports proposals rather than results: `Applied` becomes `Proposed` with a tier per finding, `Removed` becomes `Proposed removals` with both proof answers still required, and net line movement is stated as an estimate.

### Removed

- `simplify` — drop the `code-review-graph` MCP integration: the availability gate, the per-lens tool dispatch, and the reference playbook are gone, so a pass behaves the same with or without the plugin installed. `refactor` keeps its own graph integration for blast-radius analysis.

## [2.3.1] - 2026-08-09

### Changed

- `receiving-feedback` — narrow the trigger so it fires only when a message gives something to evaluate: a claim, concern, question, or rationale about an artifact (asserting a defect, questioning a decision, supplying reasoning, or proposing a change to assess), plus external review comments to assess before implementing. An unambiguous parameter choice, approval, confirmation, typo or formatting fix, or bare revision instruction that carries no claim to evaluate no longer triggers it.

## [2.3.0] - 2026-08-07

### Added

- `refactor` — new skill for behavior-preserving structural change: decomposing a function, extracting or merging a module, collapsing a layer, breaking an import cycle, renaming across the tree. The edits it takes differ from `simplify` by risk rather than size: their behavior preservation cannot be verified on the spot. It plans first with counted (not estimated) blast radius, takes approval per move rather than for the whole plan, and executes one move at a time with verification green between each, so a restructuring cannot land as a single unreviewable diff. A test edit the plan did not enumerate requires stating what the test asserted, what coupled it to structure, and what still proves the contract holds; anything less is treated as a behavior change and reverted. It accepts work from a simplify ledger, a review report, or a direct request, with no dependency on another skill.

### Changed

- `simplify` — reworked around selectable lenses, verifiability-tiered edits, and a persisted report. Scope is now a parameter (current changes by default; a file, directory, or repo when named). Five lenses (duplication, obfuscative complexity, removal, comments, semantic naming) sit behind a selection gate; the efficiency lens is retired, and correctness, security, test adequacy, and hot-path concerns route to `code-review`. Edits whose behavior preservation is verifiable now apply directly, one at a time with verification between; contract changes, spec conflicts, and the unverifiable become recorded proposals. Deletion is the default only when nothing consumes the code and no historical reason still applies, and each pass writes a dated report to `.simplify/`.

## [2.2.2] - 2026-08-07

### Changed

- `antislop-writing` — add a *performed voice* class to the AI-tell catalog: maxims stated as instruction, and abstractions or the text itself given agency, with a technical-register rule holding explanation prose to the same plainness as instructions, plus self-check and audit-checklist prompts. Figuration is judged by the work it does, not by presence, so a clarifying metaphor stays while decorative substitution is cut; the maxim and reification rules are scoped by register, and editorial writing may earn one.

## [2.2.1] - 2026-08-06

### Changed

- `sdd` (and every `sdd-*` skill), `optimize-skills`, `handoff`, and `explain-diff` — artifact prose now has a stated register. Each skill carries a `Writing Style` section asking for the voice of a professional technical writer and ASD-STE100 Simplified Technical English.

## [2.2.0] - 2026-07-31

### Changed

- `antislop-writing` — instructional passages (runbook steps, procedures, error messages) now follow ASD-STE100 Simplified Technical English: condition before command, one instruction per sentence, modals restricted to `can`/`will`/`must`, and a deliberately flat rhythm the metronome tell no longer flags. Correspondence is exempt (an email request softens on purpose), RFC 2119 keywords take precedence in normative documents, and STE's approved dictionary and tense/contraction restrictions are declined. The tell catalog and audit checklist also draw on Orwell and The Economist's style guide: press-release clichés ("game-changer," "perfect storm"), moral instruction (the closing turn from analysis to sermon), neutral reporting verbs, matching the draft's spelling dialect and date conventions, and when hedging is earned — without adopting Economist newspaper conventions (dropped serial comma, spelled-out numbers, honorifics).

## [2.1.1] - 2026-07-28

### Fixed

- `debugging` — the skill loads again. Its frontmatter description was an unquoted YAML scalar containing `Triggers: "why is this failing"`, and the bare `: ` inside it made the whole frontmatter block unparsable, so any consumer that reads the frontmatter skipped the skill entirely.

## [2.1.0] - 2026-07-28

### Breaking Changes

- Python scripts use snake_case filenames, matching PEP 8 module naming. Shipped script paths change: `build-review-packet.py` → `build_review_packet.py` (`code-review`, `simplify`), `render-dot.py` → `render_dot.py` (`optimize-skills`), `find-specs-roots.py` → `find_specs_roots.py` (`sdd`). References inside each skill are updated; update any external hook, command, or wrapper that invokes these by path.

## [2.0.3] - 2026-07-28

### Changed

- `explain-diff` — save the artifact inside the repo by default instead of requiring it live
  outside version control. Asks where to persist the file, defaulting to `.explain/` at the repo
  root (or `docs/.explain/` when the project already organizes generated docs under `docs/`), and
  offers to keep the destination untracked via the repo's root `.gitignore` or a `*` `.gitignore`
  dropped inside the directory.

## [2.0.2] - 2026-07-28

### Changed

- `commit-message` — rebalance body discipline against two failure modes instead of one. An
  orientation trigger licenses naming what a new capability does and operates on, which large
  feature commits previously had no way to say; durable-artifact routing keeps contracts and
  rationale in the specs, design docs, or ADRs that already carry them, and defers only to an
  artifact that exists at draft time. Adds a paragraph budget counted per capability rather than
  per named surface, a repo-calibration step, a rule that a docstring or error message carried in
  the diff closes the gap so no body line survives on top of it, explicit precedence of routing
  over a fired trigger, and a Commit Train path for work landing as several commits.

### Fixed

- `commit-message` — retrieve staged changes with `git diff --cached` or the harness's own SCM
  tooling. The step previously named `get_changed_files`/`repositoryPath`, a different harness's
  primitive that never existed here, so every run silently fell through to the fallback. The step
  now also directs paging through a diff that exceeds one tool call's output limit, which a long
  diff would otherwise truncate into a message that reads complete.

## [2.0.1] - 2026-07-18

### Changed

- `receiving-feedback` — tighten pushback discipline: an evidence-symmetry hard gate makes a
  declination carry the same empirical burden as an acceptance (probe a testable finding before
  pushing back); a repeat finding from an independent reviewer escalates scrutiny instead of
  being answered by precedent; prior decisions are context to re-examine, never ground truth in
  a dispute about that decision; and a flawed proposed fix no longer discredits the defect it
  addresses. Description now also triggers on "review" and "commentary".

## [2.0.0] - 2026-07-14

### Breaking Changes

- Removed the `good-prose` skill — superseded by `antislop-writing`, which subsumes its scope.
  Update any direct invocations (`/good-prose` → `/antislop-writing`); references in `proof`,
  `deep-research`, `receiving-feedback`, `interactive-notebook-demo`, `editorial-review`, and
  `synthesize` now point to `antislop-writing`.

### Added

- `antislop-writing` skill — write, rewrite, or line-edit prose so it reads as a professional
  wrote it, not a model. Adds per-register modules (technical, editorial, correspondence), a
  signed-exemplars anchor, a leveled AI-tells catalog (each tell tagged strip or rewrite), a
  fact-inventory compose workflow, and a `prose_audit.py` mechanical tripwire scanner. Replaces
  `good-prose`.

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
[2.0.0]: https://github.com/ahgraber/skills/compare/skills-v1.1.0...skills-v2.0.0
[2.0.1]: https://github.com/ahgraber/skills/compare/skills-v2.0.0...skills-v2.0.1
[2.0.2]: https://github.com/ahgraber/skills/compare/skills-v2.0.1...skills-v2.0.2
[2.0.3]: https://github.com/ahgraber/skills/compare/skills-v2.0.2...skills-v2.0.3
[2.1.0]: https://github.com/ahgraber/skills/compare/skills-v2.0.3...skills-v2.1.0
[2.1.1]: https://github.com/ahgraber/skills/compare/skills-v2.1.0...skills-v2.1.1
[2.2.0]: https://github.com/ahgraber/skills/compare/skills-v2.1.1...skills-v2.2.0
[2.2.1]: https://github.com/ahgraber/skills/compare/skills-v2.2.0...skills-v2.2.1
[2.2.2]: https://github.com/ahgraber/skills/compare/skills-v2.2.1...skills-v2.2.2
[2.3.0]: https://github.com/ahgraber/skills/compare/skills-v2.2.2...skills-v2.3.0
[2.3.1]: https://github.com/ahgraber/skills/compare/skills-v2.3.0...skills-v2.3.1
[2.3.2]: https://github.com/ahgraber/skills/compare/skills-v2.3.1...skills-v2.3.2
[2.4.0]: https://github.com/ahgraber/skills/compare/skills-v2.3.2...skills-v2.4.0
[unreleased]: https://github.com/ahgraber/skills/compare/skills-v2.4.0...HEAD
