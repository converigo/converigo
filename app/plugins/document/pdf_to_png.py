"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PDF -> PNG Plugin (Batch 2)
"""

from pathlib import Path

from app.plugins.base import ConverterPlugin


class PDFToPNGPlugin(ConverterPlugin):
    slug = "pdf-to-png"
    name = "PDF to PNG"
    description = "Convert PDF documents into PNG images page by page."
    category = "document"
    engine = "document"
    icon = "🖼️"

    source_formats = ["pdf"]
    target_formats = ["png"]

    goal = "document"
    use_case = "Best for turning PDF pages into image files for sharing and previewing."
    priority = 75
    quality = 90
    compatibility = 85
    estimated_saving = 10
    badge = "Page Images"
    seo_title = "PDF to PNG Converter | Converigo"
    seo_description = "Convert PDF documents into PNG images quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
        output_dir: Path | None = None,
        temp_dir: Path | None = None,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFToPNGPlugin only supports PDF -> PNG.")

        from app.core.settings import settings

        working_dir = temp_dir or output_dir or (settings.OUTPUT_DIR / "document")
        working_dir.mkdir(parents=True, exist_ok=True)

        # The document engine has no PNG target, so render here with PyMuPDF
        # (same pipeline as the engine's PDF -> JPG path).
        try:
            import fitz
        except ImportError as exc:
            raise RuntimeError("PyMuPDF is required for PDF to PNG conversion.") from exc

        output_path = working_dir / f"{source_path.stem}_page_01.png"

        doc = fitz.open(str(source_path))
        try:
            if doc.page_count == 0:
                raise RuntimeError("No pages were found in the PDF.")

            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pix.pil_save(str(output_path), format="PNG")
        finally:
            doc.close()

        if not output_path.exists():
            raise RuntimeError("PDF to PNG conversion did not produce output.")

        return output_path
