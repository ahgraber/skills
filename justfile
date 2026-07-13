# skills repo tasks. Run `just` (or `just --list`) to see recipes.
# Requires: uv-ship (release) — comes from ~/.local/bin (`uv tool install uv-ship`).
#
# This repo ships two independently versioned components (see AGENTS.md → Versioning & releases):
#   • skills collection  — no code version; hand-cut `skills-v<X.Y.Z>` tag on the root CHANGELOG.
#   • skills-mcp package  — `uv-ship`, tagged `skills-mcp-v<X.Y.Z>`. See skills-mcp/RELEASING.md.

# List available recipes
default:
    @just --list

# --- skills-mcp (uv-ship) --------------------------------------------------
# uv-ship needs `--config pyproject.toml` here: run from the repo root it would infer
# config from the pyproject-less git root, defaulting the tag prefix / commit message.
# The recipes below cd into skills-mcp/ and pass --config for you. See skills-mcp/RELEASING.md.

# Preview skills-mcp's pending changelog section (commits since the last skills-mcp-v* tag)
mcp-changelog:
    cd skills-mcp && uv-ship --config pyproject.toml log --latest

# Dry-run a skills-mcp release, e.g. `just mcp-release-dry patch`
mcp-release-dry bump="minor":
    cd skills-mcp && uv-ship --config pyproject.toml --dry-run next {{ bump }}

# Cut a skills-mcp release (interactive), e.g. `just mcp-release minor`
mcp-release bump="minor":
    cd skills-mcp && uv-ship --config pyproject.toml next {{ bump }}

# Set skills-mcp to an explicit version, e.g. `just mcp-release-version 1.0.0`
mcp-release-version version:
    cd skills-mcp && uv-ship --config pyproject.toml version {{ version }}

# HEAD must be skills-mcp's `bump(skills-mcp): …` commit; typically used when the pyproject version was missed.
# Fold a left-behind file into skills-mcp's latest bump commit and move its tag (force-push)
mcp-fix-release:
    #!/usr/bin/env bash
    set -eo pipefail
    version="$(sed -nE 's/^version = "([^"]+)"/\1/p' skills-mcp/pyproject.toml | head -n1)"
    if [ -z "${version}" ]; then echo "could not read version from skills-mcp/pyproject.toml" >&2; exit 1; fi
    tag="skills-mcp-v${version}"
    branch="$(git rev-parse --abbrev-ref HEAD)"
    git add skills-mcp/pyproject.toml
    git agent-commit --amend --no-edit
    git tag -f -a "${tag}" -m "$(git log -1 --format=%s)"
    git push --force-with-lease origin "${branch}"
    git push --force origin "${tag}"

# --- skills collection (manual tag) ----------------------------------------
# The collection has no code version, so uv-ship does not apply. Update the root
# CHANGELOG.md (promote [Unreleased] → the version), commit, then cut the tag here.

# Tag a skills-collection release from the root CHANGELOG, e.g. `just tag-skills 1.2.0`
tag-skills version:
    git tag -a "skills-v{{ version }}" -m "skills-v{{ version }}"
    @echo "Created skills-v{{ version }} — push with: git push origin skills-v{{ version }}"
