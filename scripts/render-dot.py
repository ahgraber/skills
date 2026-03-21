#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = []
# ///
"""Render GraphViz diagrams from .dot files or Markdown ```dot blocks."""

import argparse
from pathlib import Path
import re
import shutil
import subprocess

HEADING_PATTERN = re.compile(r"^\s{0,3}(#{1,6})\s+(.+?)\s*$")
DOT_FENCE_START_PATTERN = re.compile(r"^\s*```+\s*dot\s*$", re.IGNORECASE)
FENCE_END_PATTERN = re.compile(r"^\s*```+\s*$")
UNSAFE_FILENAME_CHARS = re.compile(r"[^a-z0-9._-]+")
SEPARATOR_RUNS = re.compile(r"[-_.]{2,}")


def require_dot() -> None:
    """Ensure the GraphViz `dot` executable is available on PATH."""
    if shutil.which("dot"):
        return
    message = (
        "GraphViz 'dot' executable not found on PATH.\n"
        "Install GraphViz (system package) and retry.\n"
        "Note: Python packages like 'graphviz' still require the 'dot' binary."
    )
    raise SystemExit(message)


def slugify_title(title: str, fallback: str) -> str:
    """Convert a section title into a filesystem-safe filename stem."""
    normalized = title.strip().lower()
    normalized = normalized.replace("&", " and ")
    normalized = UNSAFE_FILENAME_CHARS.sub("-", normalized)
    normalized = SEPARATOR_RUNS.sub("-", normalized)
    normalized = normalized.strip("._-")
    return normalized or fallback


def find_skill_dir(path: Path) -> Path:
    """Find the nearest ancestor directory containing SKILL.md."""
    start = path if path.is_dir() else path.parent
    for candidate in [start, *start.parents]:
        if (candidate / "SKILL.md").is_file():
            return candidate
    raise SystemExit(f"Could not find skill directory (no SKILL.md) above: {path}")


def ensure_writable_outputs(out_paths: list[Path], force: bool) -> None:
    """Fail if outputs already exist and --force is not set."""
    duplicates = len({path.name for path in out_paths}) != len(out_paths)
    if duplicates:
        names = [path.name for path in out_paths]
        raise SystemExit(
            "Refusing to write outputs because inferred names collide:\n" + "\n".join(f"  - {name}" for name in names)
        )

    existing = [path for path in out_paths if path.exists()]
    if existing and not force:
        raise SystemExit(
            "Refusing to overwrite existing output(s). Re-run with -f/--force:\n"
            + "\n".join(f"  - {path}" for path in existing)
        )


def render_dot_file(dot_path: Path, out_path: Path) -> None:
    """Render a .dot file to SVG."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # noqa: S603
        ["dot", "-Tsvg", str(dot_path), "-o", str(out_path)],
        check=True,
    )


def render_dot_content(dot_content: str, out_path: Path) -> None:
    """Render DOT source text to SVG."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(  # noqa: S603
        ["dot", "-Tsvg", "-o", str(out_path)],
        input=dot_content,
        text=True,
        check=True,
    )


def render_dir(dir_path: Path, out_dir: Path, force: bool) -> int:
    """Render all .dot files in a directory to SVGs in the output directory."""
    inputs = sorted(dir_path.glob("*.dot"))
    out_paths = [out_dir / f"{dot_path.stem}.svg" for dot_path in inputs]
    ensure_writable_outputs(out_paths, force)

    for dot_path, out_path in zip(inputs, out_paths, strict=True):
        render_dot_file(dot_path, out_path)
        print(f"Rendered: {out_path}")
    return len(inputs)


def extract_dot_blocks_with_headings(md_path: Path) -> list[tuple[str, str]]:
    """Extract DOT code fences and attach each to the nearest prior heading."""
    lines = md_path.read_text(encoding="utf-8").splitlines()
    fallback_heading = md_path.stem
    current_heading = fallback_heading
    blocks: list[tuple[str, str]] = []

    in_dot_block = False
    block_lines: list[str] = []
    block_heading = fallback_heading

    for line in lines:
        if in_dot_block:
            if FENCE_END_PATTERN.match(line):
                content = "\n".join(block_lines).strip()
                if content:
                    blocks.append((block_heading, content))
                in_dot_block = False
                block_lines = []
                continue
            block_lines.append(line)
            continue

        heading_match = HEADING_PATTERN.match(line)
        if heading_match:
            current_heading = heading_match.group(2).strip()
            continue

        if DOT_FENCE_START_PATTERN.match(line):
            in_dot_block = True
            block_lines = []
            block_heading = current_heading

    return blocks


def assign_markdown_output_paths(md_path: Path, assets_dir: Path) -> list[tuple[str, Path]]:
    """Infer output SVG names from nearest section headings."""
    blocks = extract_dot_blocks_with_headings(md_path)
    if not blocks:
        return []

    counts: dict[str, int] = {}
    for heading, _ in blocks:
        stem = slugify_title(heading, fallback=md_path.stem)
        counts[stem] = counts.get(stem, 0) + 1

    offsets: dict[str, int] = {}
    planned: list[tuple[str, Path]] = []
    for heading, content in blocks:
        stem = slugify_title(heading, fallback=md_path.stem)
        offsets[stem] = offsets.get(stem, 0) + 1
        if counts[stem] > 1:
            stem = f"{stem}-{offsets[stem]}"
        planned.append((content, assets_dir / f"{stem}.svg"))

    return planned


def render_markdown(md_path: Path, assets_dir: Path, force: bool) -> int:
    """Render DOT code fences found in a Markdown file."""
    markdown = md_path.read_text(encoding="utf-8")
    del markdown  # Not needed after read-path validation.
    planned = assign_markdown_output_paths(md_path, assets_dir)

    if not planned:
        print(f"No ```dot blocks found in {md_path}")
        return 0

    ensure_writable_outputs([path for _, path in planned], force)
    print(f"Found {len(planned)} diagram(s) in {md_path}")
    for content, svg_path in planned:
        render_dot_content(content, svg_path)
        print(f"Rendered: {svg_path}")
    return len(planned)


def main() -> None:
    """CLI entrypoint for rendering diagrams to skill assets."""
    parser = argparse.ArgumentParser(description="Render .dot files or Markdown ```dot blocks to SVG.")
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a .dot file, .md file, or directory of .dot files",
    )
    parser.add_argument("-f", "--force", action="store_true", help="Overwrite existing output SVG files")

    args = parser.parse_args()
    input_path = args.input.resolve()

    require_dot()
    skill_dir = find_skill_dir(input_path)
    assets_dir = skill_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    if input_path.is_dir():
        rendered = render_dir(input_path, assets_dir, args.force)
        if rendered == 0:
            print(f"No .dot files found in {input_path}")
        return

    suffix = input_path.suffix.lower()
    if suffix == ".dot":
        out_path = assets_dir / f"{input_path.stem}.svg"
        ensure_writable_outputs([out_path], args.force)
        render_dot_file(input_path, out_path)
        print(f"Rendered: {out_path}")
        return

    if suffix == ".md":
        render_markdown(input_path, assets_dir, args.force)
        return

    raise SystemExit("Input must be a .dot file, .md file, or a directory containing .dot files.")


if __name__ == "__main__":
    main()
