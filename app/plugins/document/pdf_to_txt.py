"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.1.0

PDF to TXT Plugin (DOC-05 / Batch 3)

Backed by pypdf (BSD-3-Clause). Genuine text extraction, not a fake output.
"""

from pathlib import Path

from pypdf import PdfReader

from app.plugins.base import ConverterPlugin


class PDFToTXTPlugin(ConverterPlugin):
    slug = "pdf-to-txt"
    name = "PDF to TXT"
    description = "Extract text from PDF documents into a plain text file."
    category = "document"
    engine = "document"
    icon = "📝"

    source_formats = ["pdf"]
    target_formats = ["txt"]

    goal = "document"
    use_case = "Best for pulling readable text out of PDF files for editing, search, or reuse."
    priority = 77
    quality = 90
    compatibility = 85
    estimated_saving = 10
    badge = "Text Extract"
    seo_title = "PDF to TXT Converter | Converigo"
    seo_description = "Extract text from PDF files into plain TXT quickly and accurately."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFToTXTPlugin only supports PDF -> TXT.")

        from app.core.settings import settings

        working_root = temp_dir or output_dir or (settings.OUTPUT_DIR / "document")
        working_root.mkdir(parents=True, exist_ok=True)

        reader = PdfReader(str(source_path))
        if reader.is_encrypted:
            raise RuntimeError("PDF is password protected; cannot extract text.")
        if not reader.pages:
            raise RuntimeError("PDF has no pages to extract text from.")

        output_path = working_root / f"{source_path.stem}.txt"
        text_parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)
        output_path.write_text("\n\n".join(text_parts), encoding="utf-8")

        if not output_path.exists():
            raise RuntimeError("PDF to TXT conversion did not produce output.")
        return output_path