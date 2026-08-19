#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "mermaidx[rust]>=0.9",
# ]
# ///
"""Render Mermaid to SVG/PNG/PDF locally, with no network access."""

import argparse
from pathlib import Path
import sys

import mermaidx

# merman is a Rust reimplementation that renders in milliseconds; quickjs runs the
# real mermaid.js and covers the syntax merman's stricter parser turns away.
FAST_BACKEND = "merman"
REFERENCE_BACKEND = "quickjs"


def _read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _render(source: str):
    """Return a rendered diagram, preferring the fast backend.

    Rendering is lazy, so the SVG is forced here to settle which backend can parse
    the source before anything is written to disk. The result is cached on the
    diagram, so the later save does not render a second time.
    """
    try:
        diagram = mermaidx.render(source, backend=FAST_BACKEND)
        diagram.svg()
    except Exception:  # noqa: BLE001 - the fast backend is stricter; defer to mermaid.js
        diagram = mermaidx.render(source, backend=REFERENCE_BACKEND)
        diagram.svg()
    return diagram


def main() -> int:
    """CLI entrypoint for rendering Mermaid diagrams."""
    parser = argparse.ArgumentParser(description="Render Mermaid diagrams locally.")
    parser.add_argument("--input", "-i", help="Path to a .mmd/.md file. Reads stdin if omitted.")
    parser.add_argument("--output", "-o", required=True, help="Output file path (.svg/.png/.pdf).")
    parser.add_argument("--background", help="Background colour, e.g. 'white' or '#fff'. Transparent by default.")
    parser.add_argument("--scale", type=float, help="Scale factor for raster output.")
    args = parser.parse_args()

    source = _read_input(args.input)
    if not source.strip():
        print("No Mermaid content provided.", file=sys.stderr)
        return 2

    try:
        diagram = _render(source)
    except Exception as exc:  # noqa: BLE001 - report the renderer's own message
        print(str(exc).strip() or "Mermaid render failed.", file=sys.stderr)
        return 1

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    options = {}
    if args.background:
        options["background"] = args.background
    if args.scale:
        options["scale"] = args.scale

    try:
        diagram.save(str(out_path), **options)
    except Exception as exc:  # noqa: BLE001 - unsupported extension or unwritable path
        print(str(exc).strip() or f"Could not write {out_path}.", file=sys.stderr)
        return 1

    print(f"Rendered: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
