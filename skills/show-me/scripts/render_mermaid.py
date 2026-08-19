#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "pyppeteer>=1.0.2",
# ]
# ///
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Optional


def _read_input(path: Optional[str]) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _ensure_chromium(install: bool) -> Optional[str]:
    try:
        from pyppeteer import chromium_downloader
    except Exception:
        return None

    chrome_path = chromium_downloader.chromium_executable()
    if chrome_path and Path(chrome_path).exists():
        return chrome_path

    if not install:
        return None

    try:
        chromium_downloader.download_chromium()
    except Exception:
        return None

    chrome_path = chromium_downloader.chromium_executable()
    if chrome_path and Path(chrome_path).exists():
        return chrome_path

    return None


def _maybe_set_puppeteer_executable(env: dict, install: bool) -> None:
    # If pyppeteer is installed (via uv), use its Chromium binary for mmdc.
    chrome_path = _ensure_chromium(install)
    if chrome_path:
        env.setdefault("PUPPETEER_EXECUTABLE_PATH", chrome_path)


def main() -> int:
    """CLI entrypoint for rendering Mermaid diagrams with mmdc."""
    parser = argparse.ArgumentParser(description="Render Mermaid diagrams locally using mmdc.")
    parser.add_argument("--input", "-i", help="Path to a .mmd/.md file. Reads stdin if omitted.")
    parser.add_argument("--output", "-o", required=True, help="Output file path (.svg/.png/.pdf).")
    parser.add_argument(
        "--install-chromium",
        action="store_true",
        help="Download Chromium via pyppeteer if missing.",
    )
    args = parser.parse_args()

    mmdc = shutil.which("mmdc")
    if not mmdc:
        print("mmdc not found on PATH. Install Mermaid CLI locally to render.", file=sys.stderr)
        return 2

    mermaid_src = _read_input(args.input)
    if not mermaid_src.strip():
        print("No Mermaid content provided.", file=sys.stderr)
        return 2

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmpdir:
        in_path = Path(tmpdir) / "input.mmd"
        in_path.write_text(mermaid_src, encoding="utf-8")

        try:
            env = os.environ.copy()
            _maybe_set_puppeteer_executable(env, args.install_chromium)
            subprocess.run(  # noqa: S603
                [mmdc, "-i", str(in_path), "-o", str(out_path)],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=env,
            )
        except subprocess.CalledProcessError as exc:
            err = exc.stderr.strip() or "Mermaid render failed."
            print(err, file=sys.stderr)
            return 1

    print(f"Rendered: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
