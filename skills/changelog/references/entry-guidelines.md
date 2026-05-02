# Entry Guidelines

## Include / Exclude Heuristics

### Include (user-visible)

- New user-facing features, commands, flags, options, endpoints
- Behavior changes that affect output, defaults, or UX
- Bug fixes that affected users in production
- Runtime dependency version bumps (may affect behavior or security)
- Config or environment changes that affect deployment
- Security patches or vulnerability fixes
- Deprecation notices
- Removals of any public API surface

### Exclude (internal / invisible)

- CI/CD config changes (`.github/`, `.gitlab-ci.yml`, `Makefile` targets for dev)
- Dotfile updates (`.gitignore`, `.editorconfig`, `.prettierrc`)
- Formatting or whitespace-only changes
- Test additions or fixes with no behavior change
- Dev-only dependency bumps (linters, formatters, test runners)
- Internal refactors with zero user-visible surface change
- Merge commits, version bump commits, changelog commits themselves
- "WIP", "fix typo", "cleanup" commits with no user impact

**Heuristic:** If a user reading the changelog would not care, cut it.

### Edge cases

- `docs/` changes: include only if they fix documentation the user relies on (e.g., API reference, config schema).
  Exclude purely internal notes.
- `refactor`: include if it changes timing, memory, observable error messages, or public API shape.
  Exclude if purely internal.
- `perf`: include if the improvement is meaningful and user-observable.
  Exclude micro-optimizations.

---

## Conventional Commits → Changelog Category

| Commit type / footer                     | Changelog category                   |
| ---------------------------------------- | ------------------------------------ |
| `feat`                                   | Added                                |
| `fix`                                    | Fixed                                |
| `perf`                                   | Changed                              |
| `refactor` (user-visible)                | Changed                              |
| `docs` (user-facing)                     | Changed or Added                     |
| `deprecated` or deprecation note in body | Deprecated                           |
| `BREAKING CHANGE` footer or `!` suffix   | Breaking Changes (subsection, first) |
| `chore`, `ci`, `build`, `test`, `style`  | **Excluded**                         |

When commits don't follow Conventional Commits, apply the include/exclude heuristics above and assign the category that best fits the user-observable outcome.

---

## Consolidation Rules

- A feature that landed across multiple commits → **one** `Added` entry
- A dependency bumped multiple times in the range → **one** `Changed` entry at the final version
- A fix with a follow-up "fix the fix" commit → **one** `Fixed` entry describing the resolved behavior

The goal is the net user-visible result, not a commit-by-commit transcript.

---

## Entry Style

|           |                                                                                            |
| --------- | ------------------------------------------------------------------------------------------ |
| Verb      | Imperative present tense: `Add`, `Fix`, `Remove`, `Change`, `Deprecate`                    |
| Subject   | Name the thing precisely: flag name, endpoint, method, config key                          |
| Breaking  | State what broke **and** the migration: `Remove X — replace with Y; see docs/migration.md` |
| Reference | One link per entry, prefer PR > commit hash > issue                                        |
| Length    | One line preferred; two lines max for complex breaking changes                             |

**Good:** `Fix null pointer when config file is absent on first run`
**Bad:** `fixed some stuff with config loading` / `Config file null pointer exception fix`
