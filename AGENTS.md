# AGENTS.md

This repo holds [Agent Skills](https://agentskills.io/home), folders of instructions, scripts, and resources - typically encoding procedural knowledge - that agents can discover and use to do things more accurately and efficiently.

See `skills/ai-skills` for best practices on designing skills.

Avoid adding extra documentation files inside skills unless explicitly required.

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

## Testing

- Prefer running tests and scripts inside the devshell.
- Example (mermaid validation/render):
  - `nix develop -c skills/mermaid/scripts/validate_mermaid.py --install-chromium <<'EOF'`
  - `nix develop -c scripts/render-dot.py skills/optimize-skills/references/skill-workflow.dot`

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
