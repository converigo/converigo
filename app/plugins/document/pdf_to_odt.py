"""
PDF -> ODT Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class PDFToODTPlugin(ConverterPlugin):
    slug = "pdf-to-odt"
    name = "PDF to ODT"
    description = "Convert PDF files into ODT documents."
    category = "document"
    engine = "document"
    icon = "📄"

    source_formats = ["pdf"]
    target_formats = ["odt"]

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFToODTPlugin only supports PDF -> ODT.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
