# AGENTS.md

This repo holds [Agent Skills](https://agentskills.io/home), folders of instructions, scripts, and resources - typically encoding procedural knowledge - that agents can discover and use to do things more accurately and efficiently.

See `skills/ai-skills` for best practices on designing skills.

Avoid adding extra documentation files inside skills unless explicitly required.

## Development vs. user environment

- These practices describe how we develop and test skills in this repo.
- Do not assume end users who install skills have the same tools available; only `uv` is a required runtime dependency (per the README).
- When documenting or scripting behavior, distinguish between developer-only tooling (devshell, `mmdc`, `dot`, `nix`) and what a skill user can be expected to have.

## Dev environment

- Prefer working inside the Nix devshell for tool availability (e.g., `mmdc`, `dot`).
- Enter the shell with:
  - `nix --extra-experimental-features 'nix-command flakes' develop`
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
  - `nix --extra-experimental-features 'nix-command flakes' develop -c skills/mermaid/scripts/validate_mermaid.py --install-chromium <<'EOF'`
  - `nix --extra-experimental-features 'nix-command flakes' develop -c skills/mermaid/scripts/render_mermaid.py --install-chromium -o /tmp/mermaid.svg <<'EOF'`
