# Conventional Commit Rules

## Contents

- Subject Line (Required)
- Body (Optional)
- Footers
- Output Contract
- Examples

Use this format:

```text
<type>[optional scope][!]: <description>

[optional body]

[optional footer(s)]
```

## Subject Line (Required)

Format: `<type>[optional scope][!]: <description>`

### Type

Choose the most specific type:

- `feat`: new user-facing feature or capability
- `fix`: bug fix correcting incorrect behavior
- `refactor`: code restructuring without feature/bug behavior change
- `test`: test-only changes
- `docs`: documentation-only changes
- `style`: formatting/style-only changes with no logic change
- `build`: build tooling, dependencies, packaging
- `ci`: CI/CD pipeline or config changes
- `chore`: maintenance/tooling/repo upkeep not fitting other types
- `revert`: reverts a previous commit

### Scope

Optional but recommended:

- Use a short lowercase area (`api`, `cli`, `auth`, `db`, `docs`, `deps`).
- Derive from module names or file paths.
- Omit only when no clear scope exists.

### Breaking Changes

If breaking:

- Add `!` in subject (`feat(api)!: ...`).
- Add `BREAKING CHANGE:` footer with migration guidance.

### Description

The subject is the reader's signal in scan-mode (`git log`, `git blame`, bisect) — write it so a reader scanning history can recognize whether this commit may answer their question without opening it.

- Imperative, present tense (`add`, `fix`, `update`).
- Start lowercase unless proper noun requires uppercase.
- Target 50 chars; hard limit 72 chars.
- No trailing period.
- Name the area and effect concretely — "fix off-by-one in pagination cursor", not "fix bug in pagination".

## Body

### The cold-reader test

Your reader meets this commit in two phases:

- **Scan mode** — in `git log`, `git blame`, or a bisect, they see the subject and decide whether to open it.
- **Read mode** — once opened, they read the diff to understand what changed.

The **subject** carries scan mode (see § Subject Line).
The **body** exists only when read-mode leaves a question unanswered: the diff shows what changed and where, but it does not show:

- **Why this choice** — when the subject names a choice but not the constraint that forced it.
- **Tuning rationale** — magic numbers, thresholds, or tunables a future reader will want to revisit.
- **Wrong-fix guards** — foreseeable "fixes" that would re-break the change.
- **Cross-cutting impact** — callers, consumers, or schema implications the diff doesn't reach.
- **External references** — issues, advisories, RFCs.

If no gap exists, ship subject-only.
If a gap exists, write only what fills it.
Conversation weight is not reader weight: what felt load-bearing in the dialogue is rarely what the diff fails to convey.

### Rules

- One blank line between subject and body.
- Wrap lines at 72 chars.
- **Organize by logical/topical concern** — one entry per theme, not per file or function.
  Do not use label-style section headers (`Topic: content`, `**Label**:`, etc.).
- **State outcomes, not mechanisms** — drop implementation detail the reader doesn't need to act on.
- **Never reference ephemeral scaffolding** — task IDs, group numbers, sprint names, todo-list item numbers, or other planning-artifact identifiers that won't persist after the work concludes.
  Describe _what changed and why_; where it came from in the task list is irrelevant to future readers.
- **Format freely:** bullets may aid scannability for multi-part changes; a short paragraph works when the change is a single cohesive thought.
  Either is acceptable.

## Footers

Include when applicable:

- Breaking changes:

```text
BREAKING CHANGE: <what broke and how to migrate>
```

- Issue references:

  - `Closes #123`
  - `Fixes #456`
  - `Refs #789`

- AI assistant footer (required always):

```text
AI-assistant: <AGENT>
```

Use the active agent identity for `<AGENT>` (for example, `OpenAI Codex`).

## Output Contract

- Return only the commit message in one markdown code block.
- No explanation, labels, or commentary before/after.
- Output must be directly usable with `git commit -F -`.

## Examples

**Don't** — verbose, file-per-change, label-style headers:

```text
refactor(skills-mcp): harden instructions surface, simplify internals, track lockfile

Security:
- Validate skill names in _format_skill_index against an allowlist regex, reject names
  containing the "--" namespace separator, and strip "**" — prevents prompt injection
  via crafted SKILL.md frontmatter
- Defer `project` root from import-time Path.cwd() to discover_roots() call time
- Assert _skill_info is not None in NamespacedSkillProvider; expand _discover_skills
  except clause to (OSError, AssertionError)

Instructions & docs:
- Prepend "Using Skills" rule block and skills__list_resources call-to-action to the
  MCP instructions field; append stale-index note for --reload sessions
- Document empty-roots Path.cwd() fallback and --reload index staleness in README

KISS/YAGNI:
- Remove DedupReport; dedup_skills() returns list[ResolvedSkill] directly, counters
  kept as locals for DEBUG logging
- Drop ResolvedSkill.canonical_name (never read outside dedup.py)
- Inline hardcoded "--" separator; remove namespace_separator parameter chain
- Remove require_exists parameter from discover_roots (was always True)
- Merge _run_dedup into _discover_skills; correct misleading hasattr guard comment
- Fix tautological assertion in test_parse_env_roots_empty

Build:
- Track uv.lock (removed from .gitignore per supply-chain hardening)

AI-assistant: Claude Code
```

**Do** — outcomes over mechanisms, internal changes collapsed:

```text
refactor(skills-mcp): harden instructions surface, simplify internals, track lockfile

Skill names are now validated against an allowlist regex before being
included in the index, closing a prompt-injection path through crafted
SKILL.md frontmatter.

The MCP instructions field gains a preamble explaining how to use
skills and when to call the list-resources tool.

Removed overcomplex abstractions.

AI-assistant: Claude Code
```

### Simple feature

```text
feat(cli): add verbose logging flag

AI-assistant: OpenAI Codex
```

### Subject-only, non-trivial change

```text
refactor(sdd-translate): preserve build-order in proposal scope

AI-assistant: Claude Code
```

No triggers fire — the subject names the behavior change, and the diff carries the rest.

### Bug fix with context

```text
fix(api): prevent race condition in token refresh

The token refresh endpoint was not thread-safe, causing occasional
authentication failures under high load.

Fixes #234
AI-assistant: Claude Code
```

### Breaking change

```text
feat(auth)!: migrate to OAuth 2.0

BREAKING CHANGE: Legacy API key authentication is removed.
Clients must migrate to OAuth 2.0; see docs/migration-guide.md.

Closes #567
AI-assistant: Github Copilot
```
