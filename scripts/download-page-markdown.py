#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.13"
# dependencies = [
#   "docling",
#   "markitdown",
#   "simhash",
# ]
# ///
"""Download a web page and write Markdown output."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
import re
from urllib.parse import urlparse

logger = logging.getLogger(__name__)
MAX_TITLE_LENGTH = 120


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Download web pages and save them as Markdown.",
    )
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument(
        "-f",
        "--file",
        type=Path,
        help="Path to a newline-delimited URL list.",
    )
    source_group.add_argument(
        "-u",
        "--url",
        nargs="+",
        help="Single URL string to convert.",
    )
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        help="Output directory for markdown files.",
    )
    parser.add_argument(
        "--engine",
        choices=("auto", "docling", "markitdown"),
        default="auto",
        help="Conversion engine to use (default: auto).",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing files when a name collision occurs.",
    )
    return parser.parse_args()


def configure_logging() -> None:
    """Configure logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def is_url(value: str) -> bool:
    """Return True when the input is an http(s) URL."""
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def load_urls_from_file(path: Path) -> list[str]:
    """Load newline-delimited URLs from a text file."""
    lines = path.read_text(encoding="utf-8").splitlines()
    urls = [line.strip() for line in lines if line.strip() and not line.strip().startswith("#")]
    if not urls:
        raise ValueError(f"No URLs found in {path}")
    return urls


def slugify(value: str) -> str:
    """Convert text into a kebab-case slug."""
    value = value.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def extract_title(markdown: str, url: str) -> str | None:
    """Infer a descriptive title from markdown content."""
    title = extract_title_from_frontmatter(markdown)
    if title:
        return title

    title = extract_title_from_link_line(markdown)
    if title:
        return title

    heading_pattern = re.compile(r"^#{1,6}\s+(.+?)\s*(?:#+\s*)?$")
    headings: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = heading_pattern.match(stripped)
        if match:
            headings.append(match.group(1).strip())

    if not headings:
        return None

    hinted = pick_heading_by_url_hint(headings, url)
    if hinted:
        return hinted

    return headings[0]


def extract_title_from_frontmatter(markdown: str) -> str | None:
    """Extract a title from YAML frontmatter, when present."""
    lines = markdown.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for line in lines[1:40]:
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.lower().startswith("title:"):
            return stripped.split(":", 1)[1].strip().strip('"')
    return None


def extract_title_from_link_line(markdown: str) -> str | None:
    """Extract a title from a top-level markdown link line."""
    for line in markdown.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^\[(.+?)\]\((https?://[^\s]+)\)$", stripped)
        if match:
            return match.group(1).strip()
        break
    return None


def pick_heading_by_url_hint(headings: list[str], url: str) -> str | None:
    """Pick the heading that best matches URL path tokens."""
    parsed = urlparse(url)
    tokens: list[str] = []
    for segment in parsed.path.split("/"):
        segment = segment.strip()
        if not segment:
            continue
        tokens.extend(re.split(r"[^a-zA-Z0-9]+", segment))

    tokens = [token.lower() for token in tokens if token]
    if not tokens:
        return None

    for heading in headings:
        heading_lower = heading.lower()
        if all(token in heading_lower for token in tokens if len(token) > 2):
            return heading
        for token in tokens:
            if token and token in heading_lower:
                return heading
    return None


def contents_differ(existing: str, new: str) -> bool:
    """Return True when two markdown blobs are substantially different."""
    if existing == new:
        return False
    from simhash import Simhash

    return Simhash(existing).distance(Simhash(new)) > 3


def build_base_name(title: str, domain: str, counter: int, max_len: int) -> str:
    """Build a kebab-case base filename with a domain tag."""
    safe_title = slugify(title) or "page"
    safe_domain = domain or "page"
    counter_suffix = f"-{counter}" if counter > 1 else ""
    tag = f"[{safe_domain}]"
    available = max_len - len(counter_suffix) - len(tag) - 1
    if available < 1:
        available = 1
    trimmed_title = safe_title[:available]
    trimmed_title = trimmed_title.rstrip("-") or "page"
    return f"{trimmed_title}{counter_suffix}-{tag}"


def resolve_output_path(outdir: Path, url: str, title: str | None) -> Path:
    """Resolve the output path for a URL and inferred title."""
    outdir.mkdir(parents=True, exist_ok=True)
    domain = urlparse(url).netloc or "page"
    base_title = title or domain
    base_name = build_base_name(base_title, domain, 1, MAX_TITLE_LENGTH)
    return outdir / f"{base_name}.md"


def convert_with_docling(url: str) -> str:
    """Convert a URL to markdown using Docling."""
    from docling.datamodel.base_models import ConversionStatus
    from docling.document_converter import DocumentConverter

    converter = DocumentConverter()
    result = converter.convert(url)
    status = getattr(result, "status", None)
    if status is not None and status != ConversionStatus.SUCCESS:
        raise RuntimeError(f"Docling conversion failed with status {status}")
    return result.document.export_to_markdown()


def convert_with_markitdown(url: str) -> str:
    """Convert a URL to markdown using MarkItDown."""
    from markitdown import MarkItDown

    converter = MarkItDown(enable_plugins=False)
    result = converter.convert(url)
    return result.text_content


def convert_url(url: str, engine: str) -> tuple[str, str]:
    """Convert a URL to markdown using the selected engine."""
    if engine in {"auto", "docling"}:
        try:
            return convert_with_docling(url), "docling"
        except Exception:
            if engine == "docling":
                raise
            logger.info("Docling failed for %s, falling back to MarkItDown.", url)

    return convert_with_markitdown(url), "markitdown"


def main() -> None:
    """Run the CLI entrypoint."""
    configure_logging()
    args = parse_args()

    if args.file:
        urls = load_urls_from_file(args.file)
    else:
        invalid = [value for value in args.url if not is_url(value)]
        if invalid:
            raise ValueError("--url must contain valid http(s) URLs.")
        urls = args.url
    multi = len(urls) > 1

    if args.outdir is None:
        if multi:
            raise ValueError("--outdir is required when converting multiple URLs.")
        markdown, _engine = convert_url(urls[0], args.engine)
        print(markdown)
        return

    for url in urls:
        markdown, engine = convert_url(url, args.engine)
        title = extract_title(markdown, url)
        output_path = resolve_output_path(args.outdir, url, title)
        if output_path.exists():
            existing = output_path.read_text(encoding="utf-8")
            if contents_differ(existing, markdown):
                if args.overwrite:
                    logger.warning("Overwriting existing file %s", output_path)
                else:
                    logger.warning("Collision detected for %s; skipping.", output_path)
                    continue
            else:
                logger.info("Output already up to date at %s", output_path)
                continue
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        logger.info("Wrote %s output to %s", engine, output_path)


if __name__ == "__main__":
    main()
