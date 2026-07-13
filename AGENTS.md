# AGENTS.md

This repo holds [Agent Skills](https://agentskills.io/home), folders of instructions, scripts, and resources - typically encoding procedural knowledge - that agents can discover and use to do things more accurately and efficiently.

See `skills/ai-skills` for best practices on designing skills.

Avoid adding extra documentation files inside skills unless explicitly required.

## Source skills vs. installed skills

- This repo is the **upstream source** for the skills it contains.
  The agent assisting on this repo may have overlapping skills installed (visible in its available-skills list); those installed copies are downstream consumers and may be stale or diverged.
- All work in this repo — edits, reviews, refactors, tests — must target the **repo variant** under [skills/](skills/).
  Never operate against the installed version surfaced to the agent.
- **Corollary (pressure-testing):** if the user asks to pressure-test, exercise, or critique a skill defined in this repo, work against the repo variant by reading [skills/\<name>/SKILL.md](skills/) (and its references) directly.
  Do **not** invoke the installed copy via the `Skill` tool — that loads a potentially divergent version and gives misleading results.

## Development vs. user environment

- These practices describe how we develop and test skills in this repo.
- **IMPORTANT**: Do not assume end users who install skills have the same tools available; only `uv` is a required runtime dependency (per the README).
- When documenting or scripting behavior, distinguish between developer-only tooling (devshell, `mmdc`, `dot`, `nix`) and what a user can be expected to have.

## Dev environment

- Prefer working inside the Nix devshell for tool availability (e.g., `mmdc`, `dot`).
- Enter the shell with:
  - `nix develop`
- `flake.nix` is the source of truth for devshell packages.

## Python scripts (skills/*/scripts/*.py)

- Use `uv` inline script metadata for dependencies (no `pyproject.toml`).
- Required header format:

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "package>=x.y.z",
# ]
# ///
```

- Keep scripts runnable directly; do not assume a separate venv.
- Comments and docstrings describe what exists now (or the rationale for the current design), never what the code used to be.
  No "previously…", "no longer…", "changed from…", or "renamed from…" — that history belongs in commit messages and changelogs.
  When editing, delete stale historical asides you encounter rather than preserving them.

## Testing

- Prefer running tests and scripts inside the devshell.
- Example (mermaid validation/render):
  - `nix develop -c skills/mermaid/scripts/validate_mermaid.py --install-chromium <<'EOF'`
  - `nix develop -c scripts/render-dot.py skills/optimize-skills/references/skill-workflow.dot`

### Tests for skill scripts

- Put tests at the repo root under `tests/<skill_name>/`, not inside `skills/<name>/`.
  Keeping them out of the skill directory means they are not shipped when the skill is installed.
- Write each test file as a `uv` script (the same inline-metadata header as the script under test), declaring its own dependencies (`pytest`, plus anything the script imports).
- Import the script under test by relative path, and self-run via `pytest.main(...)` in a `__main__` block with `--rootdir` and `--confcutdir` pinned to the test's own directory.
  Otherwise pytest walks the repo root and trips on sandbox-denied files such as `.env`.
- Run with `uv run tests/<skill_name>/test_<name>.py`.
- `.ruff.toml` ignores `D`, `S101`, and `S301` under `**/tests/**`, so idiomatic `assert`s and undocumented test functions pass lint.

## Versioning & releases

This repo ships **two independently versioned components**; never fold one's release into the other's.

| Component             | What it is                                       | Version source                                  | Changelog                                          | Tag prefix     | Cut with                                                           |
| --------------------- | ------------------------------------------------ | ----------------------------------------------- | -------------------------------------------------- | -------------- | ------------------------------------------------------------------ |
| **skills collection** | everything under [skills/](skills/)              | none (a doc collection — no code version)       | root [CHANGELOG.md](CHANGELOG.md)                  | `skills-v`     | manual annotated tag                                               |
| **skills-mcp**        | the Python package in [skills-mcp/](skills-mcp/) | `skills-mcp/pyproject.toml` `[project].version` | [skills-mcp/CHANGELOG.md](skills-mcp/CHANGELOG.md) | `skills-mcp-v` | `uv-ship` (see [skills-mcp/RELEASING.md](skills-mcp/RELEASING.md)) |

- Tags are namespaced so the two series never collide and `git describe` stays unambiguous: match on `skills-v*` or `skills-mcp-v*`, never bare `skills-*`.
- The repo root has no `pyproject.toml`, so the skills collection is not a package — it is versioned purely by its changelog and a hand-cut `skills-v<X.Y.Z>` tag.
  Only `skills-mcp` uses `uv-ship` / `uv version`.
- skills-mcp uses a **static** `[project].version` bumped by `uv version` (via uv-ship); do not switch it to dynamic/VCS versioning.

## Changelog

- A change to `skills-mcp` lands in [skills-mcp/CHANGELOG.md](skills-mcp/CHANGELOG.md); any other user-visible change lands in the root [CHANGELOG.md](CHANGELOG.md).
  Keep each component's entries in its own file.
- Before committing a change that would read as **Added**, **Changed**, **Deprecated**, **Removed**, or **Breaking** in the relevant `CHANGELOG.md` (new skill, new user-facing capability, renamed/removed skill, behavior change a skill user would notice) — not pure **Fixed** typo/doc/test/dev-tooling commits — invoke the `changelog` skill to draft the `[Unreleased]` entry before creating the commit.
  Pure fixes are worth a changelog entry too when they change observable behavior; skip only for CI/test-only, formatting, or repo-scaffold commits.
- Let the `changelog` skill place entries in the correct category and phrasing; do not hand-write `CHANGELOG.md` entries inline.
- Cutting a release is a separate, explicit step from routine commits — do it only when the user asks, and confirm the version number first (see `references/changelog-format.md` in the `changelog` skill for bump rules).
  For the **skills collection**, this means promoting `[Unreleased]` in the root `CHANGELOG.md` to a versioned block and hand-cutting the `skills-v<X.Y.Z>` tag.
  For **skills-mcp**, `uv-ship` handles the promotion, version bump, and `skills-mcp-v<X.Y.Z>` tag in one step — follow [skills-mcp/RELEASING.md](skills-mcp/RELEASING.md).

## Commit & Review Guidelines

- **Hard gate before committing**: before running `git agent-commit`, present the user with (1) the proposed commit message and (2) a concise diff summary covering which files changed and what each change does.
  Wait for explicit user approval; do not proceed if the user requests changes.
- **Every commit message draft, without exception, must be produced by invoking the `commit-message` skill first.**
  A prior invocation earlier in the same session does not satisfy this requirement — re-invoke for each request.
  Drafting inline, from memory, or from habit is not acceptable.
- Commit format: `type(scope): summary` (e.g., `feat(zsh): …`, `fix(vscode): …`).
  Scope should reflect directories or logical surfaces.
- Separate unrelated changes (docs vs configs vs lockfile updates) into distinct commits.
- Use `git agent-commit` (not `git commit`) to create signed commits; this alias uses the dedicated agent signing key at `~/.ssh/id_ed25519_agent_signing`.
