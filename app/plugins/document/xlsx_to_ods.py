"""
XLSX -> ODS Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class XLSXToODSPlugin(ConverterPlugin):
    slug = "xlsx-to-ods"
    name = "XLSX to ODS"
    description = "Convert XLSX spreadsheets to ODS format."
    category = "document"
    engine = "document"
    icon = "📊"

    source_formats = ["xlsx"]
    target_formats = ["ods"]

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("XLSXToODSPlugin only supports XLSX -> ODS.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
