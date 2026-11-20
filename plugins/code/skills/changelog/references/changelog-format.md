# Changelog Format Reference

Based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and [Common Changelog](https://common-changelog.org/).

## File Structure

```text
CHANGELOG.md
  [Unreleased] section (optional, accumulates in-progress entries)
  [x.y.z] - YYYY-MM-DD  (most recent release first)
  [x.y.z] - YYYY-MM-DD
  ...
  Version comparison links (bottom of file)
```

- File name: `CHANGELOG.md` (exact, at repo root)
- Encoding: UTF-8, Unix line endings
- Latest version at the top; oldest at the bottom

## Version Block Structure

```markdown
## [1.2.0] - 2026-05-02

### Breaking Changes

- Remove `--legacy-auth` flag — use `--auth-method=token` instead; see [migration guide](docs/migration.md)

### Added

- Add `--dry-run` flag to preview changes without applying them ([#42](https://github.com/owner/repo/pull/42))

### Changed

- Increase default timeout from 30s to 60s

### Deprecated

- Deprecate `--output=xml`; will be removed in v2.0.0

### Removed

- Remove Python 3.8 support

### Fixed

- Fix null pointer when config file is absent on first run ([#39](https://github.com/owner/repo/pull/39))

### Security

- Patch path traversal vulnerability in file upload handler (CVE-2026-XXXX)
```

### Rules

- Version header: `## [x.y.z] - YYYY-MM-DD` — square brackets around version, ISO 8601 date only
- Category headers: `###` level, title case, only include categories that have entries
- Breaking Changes subsection always appears first when present
- Omit empty category subsections entirely

## Unreleased Section

```markdown
## [Unreleased]

### Added

- Add support for OIDC authentication
```

- Use when accumulating entries during development before a release
- Rename to a versioned header (e.g., `## [1.3.0] - 2026-06-01`) at release time
- Write entries here at PR-merge time, not at release time — context is freshest then

## Version Comparison Links

At the bottom of the file, add comparison links for each version:

```markdown
[Unreleased]: https://github.com/owner/repo/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/owner/repo/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/owner/repo/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/owner/repo/releases/tag/v1.0.0
```

- Each version heading `[x.y.z]` becomes a link via these footer references
- Update `[Unreleased]` link whenever a new version is tagged

## Semantic Versioning Alignment

| Change type                     | Version bump      |
| ------------------------------- | ----------------- |
| Breaking change (any)           | MAJOR (`x+1.0.0`) |
| New feature, no breaking change | MINOR (`x.y+1.0`) |
| Bug fix, security patch, deps   | PATCH (`x.y.z+1`) |

If the change set contains a breaking change, the version **must** be a major bump regardless of how small the change is.

## Anti-Patterns

| Anti-pattern                              | Fix                                             |
| ----------------------------------------- | ----------------------------------------------- |
| Git log dump ("fix stuff", "wip", hashes) | Rewrite as user-outcome entries                 |
| Passive voice ("Support was added for X") | Imperative: "Add support for X"                 |
| One entry per commit for a single feature | Consolidate into one logical entry              |
| Breaking change with no migration path    | Add `— replace with Y` or link to migration doc |
| Missing version comparison links          | Add footer links for all versions               |
| Regional date format (`05/02/2026`)       | ISO 8601 only: `2026-05-02`                     |
