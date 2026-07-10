"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 3.0.0

DOCX -> PDF Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class WordToPDFPlugin(ConverterPlugin):
    slug = "word-to-pdf"
    name = "Word to PDF"
    description = "Convert DOCX documents into PDF files."
    category = "document"
    engine = "document"
    icon = "📄"

    source_formats = ["docx", "doc"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for turning Word documents into portable PDF files."
    priority = 85
    quality = 90
    compatibility = 85
    estimated_saving = 15
    badge = "Portable PDF"
    seo_title = "Word to PDF Converter | Convertin"
    seo_description = "Convert DOCX documents into PDF files quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("WordToPDFPlugin only supports DOCX/DOC -> PDF.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
