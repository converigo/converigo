"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.1

PDF Compress Plugin

Batch 5 (DOC-29) rewrite: genuine lossless PDF compression using pypdf
(BSD, already in requirements).  The previous implementation was a stub
that only copied input bytes to the output path.

Strategy (pypdf 6.16.2 API verified):
1. ``PdfWriter.append(reader)`` rebuilds the document.
2. ``page.compress_content_streams()`` deflates every page content stream
   (lossless recompression).
3. ``writer.compress_identical_objects(...)`` deduplicates identical and
   orphaned indirect objects.

Guard: the output is never larger than the input.  If recompression does
not shrink the document (already-optimized PDF), the original bytes are
returned instead so users never receive a bigger file.
"""

import logging
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.plugins.base import ConverterPlugin

logger = logging.getLogger(__name__)


class PDFCompressPlugin(ConverterPlugin):
    slug = "pdf-compress"
    name = "PDF Compress"
    description = "Compress PDF documents to reduce file size."
    category = "document"
    engine = "document"
    icon = "🗜️"

    source_formats = ["pdf"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for shrinking PDF file size for sharing and storage."
    priority = 75
    quality = 85
    compatibility = 80
    estimated_saving = 20
    badge = "Smaller Files"
    seo_title = "PDF Compress Converter | Converigo"
    seo_description = "Compress PDF files to reduce size while maintaining readability."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFCompressPlugin only supports PDF -> PDF.")

        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "document")
        working_root.mkdir(parents=True, exist_ok=True)
        output_path = working_root / f"{source_path.stem}_compressed.pdf"

        reader = PdfReader(str(source_path))
        if reader.is_encrypted:
            try:
                if not reader.decrypt(""):
                    raise RuntimeError("empty password rejected")
            except Exception as exc:
                raise RuntimeError(
                    "PDF is password protected; remove the password before compressing."
                ) from exc

        if len(reader.pages) == 0:
            raise RuntimeError("PDF has no pages to compress.")

        writer = PdfWriter()
        writer.append(reader, import_outline=True)

        # Pass 1: deflate each page content stream (lossless).
        for page in writer.pages:
            try:
                page.compress_content_streams()
            except Exception as exc:  # pragma: no cover - defensive
                logger.debug("pdf-compress: compress_content_streams skipped: %s", exc)

        # Pass 2: deduplicate identical / orphaned indirect objects.
        # (No arguments -> pypdf defaults: remove_duplicates=True,
        # remove_unreferenced=True; avoids the deprecated kwarg names.)
        try:
            writer.compress_identical_objects()
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("pdf-compress: compress_identical_objects skipped: %s", exc)

        with output_path.open("wb") as handle:
            writer.write(handle)
        writer.close()

        source_size = source_path.stat().st_size
        compressed_size = output_path.stat().st_size
        if compressed_size > source_size:
            logger.info(
                "pdf-compress: recompressed output (%d B) >= input (%d B); "
                "returning original bytes so output is never larger.",
                compressed_size,
                source_size,
            )
            output_path.write_bytes(source_path.read_bytes())

        return output_path
