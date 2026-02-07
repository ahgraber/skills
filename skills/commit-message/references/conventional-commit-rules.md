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

- Imperative, present tense (`add`, `fix`, `update`).
- Start lowercase unless proper noun requires uppercase.
- Target 50 chars; hard limit 72 chars.
- No trailing period.
- Be specific about behavior impact.

## Body (Optional)

Include a body when subject alone is insufficient.

Guidelines:

- One blank line between subject and body.
- Wrap lines at 72 chars.
- Explain what changed and why (not diff-level implementation detail).
- Use bullets for multi-part changes.
- Do not restate subject text.

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

### Simple feature

```text
feat(cli): add verbose logging flag

AI-assistant: OpenAI Codex
```

### Bug fix with context

```text
fix(api): prevent race condition in token refresh

The token refresh endpoint was not thread-safe, causing occasional
authentication failures under high load.

Fixes #234
AI-assistant: OpenAI Codex
```

### Breaking change

```text
feat(auth)!: migrate to OAuth 2.0

BREAKING CHANGE: Legacy API key authentication is removed.
Clients must migrate to OAuth 2.0; see docs/migration-guide.md.

Closes #567
AI-assistant: OpenAI Codex
```
