#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "graphviz>=0.20.3",
# ]
# ///
"""Render GraphViz .dot files to SVG using the `dot` CLI."""

import argparse
from pathlib import Path
import shutil
import subprocess

try:
    import graphviz as gv
except Exception:
    gv = None


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


def render_dot(dot_path: Path, out_path: Path) -> None:
    """Render a single .dot file to an SVG output path."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if gv is None:
        subprocess.run(  # noqa: S603
            ["dot", "-Tsvg", str(dot_path), "-o", str(out_path)],
            check=True,
        )
        return

    source = gv.Source(dot_path.read_text(encoding="utf-8"))
    source.render(
        filename=out_path.with_suffix(""),
        format="svg",
        cleanup=True,
        quiet=True,
    )


def render_dir(dir_path: Path, out_dir: Path) -> None:
    """Render all .dot files in a directory to SVGs in the output directory."""
    for dot_path in sorted(dir_path.glob("*.dot")):
        out_path = out_dir / f"{dot_path.stem}.svg"
        render_dot(dot_path, out_path)


def main() -> None:
    """CLI entrypoint for rendering .dot files."""
    parser = argparse.ArgumentParser(description="Render GraphViz .dot files to SVG using the dot CLI.")
    parser.add_argument(
        "input",
        type=Path,
        help="Path to a .dot file or a directory containing .dot files",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Output SVG file or directory (defaults to alongside input)",
    )

    args = parser.parse_args()
    input_path = args.input

    require_dot()

    if input_path.is_dir():
        out_dir = args.output if args.output else input_path
        render_dir(input_path, out_dir)
        return

    if input_path.suffix != ".dot":
        raise SystemExit("Input must be a .dot file or a directory containing .dot files.")

    out_path = args.output if args.output else input_path.with_suffix(".svg")
    render_dot(input_path, out_path)


if __name__ == "__main__":
    main()
