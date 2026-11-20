#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12,<3.15"
# dependencies = [
#   "mermaidx[rust]>=0.9",
# ]
# ///
"""Check that Mermaid source parses, using a local renderer with no network access."""

import argparse
from pathlib import Path
import sys

import mermaidx

# merman is a Rust reimplementation that parses in milliseconds; quickjs runs the
# real mermaid.js and is the authority on what counts as valid. merman is the
# stricter of the two, so its rejection is never the final answer.
FAST_BACKEND = "merman"
REFERENCE_BACKEND = "quickjs"


def _read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _parses(source: str, backend: str) -> Exception | None:
    """Return the failure from rendering `source`, or None when it parses.

    Rendering is lazy, so the SVG has to be forced for a parse error to surface.
    """
    try:
        mermaidx.render(source, backend=backend).svg()
    except Exception as exc:  # noqa: BLE001 - any failure means this backend rejected it
        return exc
    return None


def main() -> int:
    """CLI entrypoint for validating Mermaid source."""
    parser = argparse.ArgumentParser(description="Validate Mermaid source locally.")
    parser.add_argument("--input", "-i", help="Path to a .mmd/.md file. Reads stdin if omitted.")
    args = parser.parse_args()

    source = _read_input(args.input)
    if not source.strip():
        print("No Mermaid content provided.", file=sys.stderr)
        return 2

    if _parses(source, FAST_BACKEND) is None:
        print("Mermaid validation OK.")
        return 0

    # The fast backend rejected it; only mermaid.js itself can settle the question.
    failure = _parses(source, REFERENCE_BACKEND)
    if failure is None:
        print("Mermaid validation OK.")
        return 0

    print(str(failure).strip() or "Mermaid validation failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
