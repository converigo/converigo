"""
ODT -> PDF Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class ODTToPDFPlugin(ConverterPlugin):
    slug = "odt-to-pdf"
    name = "ODT to PDF"
    description = "Convert ODT files to PDF."
    category = "document"
    engine = "document"
    icon = "📄"

    source_formats = ["odt"]
    target_formats = ["pdf"]

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("ODTToPDFPlugin only supports ODT -> PDF.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
