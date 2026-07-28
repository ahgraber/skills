#!/usr/bin/env -S uv run --script
# /// script
# dependencies = [
#   "docling",
# ]
# ///
"""Convert a local file with Docling and write markdown output."""

from __future__ import annotations

import argparse
from io import BytesIO
import logging
import os
from pathlib import Path

from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.backend_options import HTMLBackendOptions, MarkdownBackendOptions
from docling.datamodel.base_models import ConversionStatus, InputFormat
from docling.datamodel.pipeline_options import ConvertPipelineOptions, ThreadedPdfPipelineOptions
from docling.document_converter import DocumentConverter, HTMLFormatOption, MarkdownFormatOption, PdfFormatOption
from docling_core.transforms.serializer.markdown import MarkdownDocSerializer, MarkdownParams
from docling_core.types.doc.base import ImageRefMode
from docling_core.types.io import DocumentStream

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert a local file with Docling and write markdown output.",
    )
    parser.add_argument("file", type=Path, help="Path to a local PDF, HTML, or Markdown file.")
    parser.add_argument(
        "-o",
        "--outfile",
        type=Path,
        help="Write markdown output to this file (defaults to stdout).",
    )
    return parser.parse_args()


def configure_logging() -> None:
    """Configure root logging to stderr at INFO level."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )


def build_converter() -> DocumentConverter:
    """Build a Docling converter with OCR, enrichment, and remote services enabled."""
    cpu_threads = os.cpu_count() or 4

    pdf_pipeline = ThreadedPdfPipelineOptions(
        ocr_batch_size=4,
        layout_batch_size=4,
        table_batch_size=4,
    )
    pdf_pipeline.accelerator_options = AcceleratorOptions(
        num_threads=cpu_threads,
        device=AcceleratorDevice.AUTO,
    )
    pdf_pipeline.enable_remote_services = True
    pdf_pipeline.do_ocr = True
    pdf_pipeline.do_picture_description = True
    pdf_pipeline.do_picture_classification = False
    pdf_pipeline.do_code_enrichment = True
    pdf_pipeline.do_formula_enrichment = True
    pdf_pipeline.generate_page_images = True
    pdf_pipeline.generate_picture_images = True
    pdf_pipeline.generate_table_images = True
    pdf_pipeline.do_table_structure = True
    pdf_options = PdfFormatOption(pipeline_options=pdf_pipeline)

    common_pipeline = ConvertPipelineOptions()
    common_pipeline.enable_remote_services = True
    common_pipeline.do_picture_description = True

    html_backend = HTMLBackendOptions(
        kind="html",
        fetch_images=True,
        enable_remote_fetch=True,
        enable_local_fetch=True,
        source_uri=None,
    )
    md_backend = MarkdownBackendOptions(
        kind="md",
        fetch_images=True,
        enable_remote_fetch=True,
        enable_local_fetch=True,
        source_uri=None,
    )

    return DocumentConverter(
        format_options={
            InputFormat.HTML: HTMLFormatOption(
                pipeline_options=common_pipeline,
                backend_options=html_backend,
            ),
            InputFormat.PDF: pdf_options,
            InputFormat.MD: MarkdownFormatOption(
                pipeline_options=common_pipeline,
                backend_options=md_backend,
            ),
        }
    )


def convert_to_markdown(converter: DocumentConverter, input_path: Path) -> str:
    """Convert the input file to markdown text, raising on conversion failure."""
    data = input_path.read_bytes()
    source = DocumentStream(name=input_path.name, stream=BytesIO(data))
    result = converter.convert(source)
    if result.status != ConversionStatus.SUCCESS:
        raise RuntimeError(f"Docling conversion failed with status {result.status}")
    serializer = MarkdownDocSerializer(
        doc=result.document,
        params=MarkdownParams(
            image_mode=ImageRefMode.PLACEHOLDER,
            image_placeholder="",
            mark_meta=True,
        ),
    )
    return serializer.serialize().text


def main() -> None:
    """Convert the input file and write markdown to the outfile or stdout."""
    configure_logging()
    args = parse_args()
    converter = build_converter()
    markdown = convert_to_markdown(converter, args.file)

    if args.outfile:
        args.outfile.parent.mkdir(parents=True, exist_ok=True)
        args.outfile.write_text(markdown, encoding="utf-8")
        logger.info("Wrote markdown to %s", args.outfile)
        return

    print(markdown)


if __name__ == "__main__":
    main()
