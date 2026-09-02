"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.1.0

PDF Merge Plugin

Backed by pypdf (BSD-3-Clause). Genuine page-level merge, not a byte copy.
"""

from pathlib import Path
from typing import List

from pypdf import PdfReader, PdfWriter

from app.plugins.base import ConverterPlugin


class PDFMergePlugin(ConverterPlugin):
    slug = "pdf-merge"
    name = "PDF Merge"
    description = "Merge multiple PDF files into a single document."
    category = "document"
    engine = "document"
    icon = "📚"

    source_formats = ["pdf"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for combining multiple PDF files into one shared document."
    priority = 75
    quality = 85
    compatibility = 80
    estimated_saving = 10
    badge = "Combine Files"
    seo_title = "PDF Merge Converter | Converigo"
    seo_description = "Merge multiple PDF files into one document quickly."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        """Single-file merge: wraps a single PDF for backward compatibility."""
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFMergePlugin only supports PDF -> PDF.")

        from app.core.settings import settings

        return await self.merge(
            [source_path],
            output_dir=output_dir,
            temp_dir=temp_dir or (settings.OUTPUT_DIR / "document"),
        )

    async def merge(
        self,
        source_paths: List[Path],
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        """Merge multiple PDFs into one. Uses pypdf for genuine page-level merge."""
        writer = PdfWriter()
        for path in source_paths:
            reader = PdfReader(str(path))
            for page in reader.pages:
                writer.add_page(page)

        working_root = temp_dir or output_dir
        if working_root is None:
            from app.core.settings import settings
            working_root = settings.OUTPUT_DIR / "document"
        working_root.mkdir(parents=True, exist_ok=True)
        output_path = working_root / "merged.pdf"
        with open(output_path, "wb") as f:
            writer.write(f)
        return output_path
