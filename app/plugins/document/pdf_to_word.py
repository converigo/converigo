"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PDF -> Word Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class PDFToWordPlugin(ConverterPlugin):
    slug = "pdf-to-word"
    name = "PDF to Word"
    description = "Convert PDF documents into editable Word files."
    category = "document"
    engine = "document"
    icon = "📄"

    source_formats = ["pdf"]
    target_formats = ["docx", "doc"]

    goal = "document"
    use_case = "Best for turning PDFs into editable Word documents."
    priority = 80
    quality = 90
    compatibility = 85
    estimated_saving = 10
    badge = "Editable DOCX"
    seo_title = "PDF to Word Converter | Converigo"
    seo_description = "Convert PDF documents into editable Word files quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFToWordPlugin only supports PDF -> DOCX/DOC.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
