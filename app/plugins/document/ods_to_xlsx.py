"""
ODS -> XLSX Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class ODSToXLSXPlugin(ConverterPlugin):
    slug = "ods-to-xlsx"
    name = "ODS to XLSX"
    description = "Convert ODS spreadsheets into XLSX format."
    category = "document"
    engine = "document"
    icon = "📊"

    source_formats = ["ods"]
    target_formats = ["xlsx"]

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("ODSToXLSXPlugin only supports ODS -> XLSX.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
