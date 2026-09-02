"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.1.0

PDF Split Plugin

Backed by pypdf (BSD-3-Clause). Genuine page-level split packaged as a ZIP
of per-page PDF files, not a byte copy.
"""

import zipfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from app.plugins.base import ConverterPlugin


class PDFSplitPlugin(ConverterPlugin):
    slug = "pdf-split"
    name = "PDF Split"
    description = "Split PDF documents into separate files."
    category = "document"
    engine = "document"
    icon = "✂️"

    source_formats = ["pdf"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for separating PDF pages into smaller documents."
    priority = 75
    quality = 85
    compatibility = 80
    estimated_saving = 10
    badge = "Split Pages"
    seo_title = "PDF Split Converter | Converigo"
    seo_description = "Split PDF files into multiple smaller documents easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFSplitPlugin only supports PDF -> PDF.")

        from app.core.settings import settings

        working_root = (temp_dir or output_dir or (settings.OUTPUT_DIR / "document"))
        working_root.mkdir(parents=True, exist_ok=True)

        reader = PdfReader(str(source_path))
        if reader.pages:
            total_pages = len(reader.pages)
        else:
            total_pages = 0
        if total_pages == 0:
            raise RuntimeError("PDF has no pages to split.")

        # Split: one PDF per page, packaged into a single ZIP archive so the
        # conversion pipeline still returns one downloadable artifact.
        zip_path = working_root / f"{source_path.stem}_split.zip"
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as archive:
            for index, page in enumerate(reader.pages, start=1):
                writer = PdfWriter()
                writer.add_page(page)
                page_path = working_root / f"{source_path.stem}_page_{index:03d}.pdf"
                with open(page_path, "wb") as f:
                    writer.write(f)
                archive.write(str(page_path), arcname=page_path.name)
                page_path.unlink(missing_ok=True)

        return zip_path
