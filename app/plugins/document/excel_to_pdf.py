"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

Excel -> PDF Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class ExcelToPDFPlugin(ConverterPlugin):
    slug = "excel-to-pdf"
    name = "Excel to PDF"
    description = "Convert Excel spreadsheets into PDF files."
    category = "document"
    engine = "document"
    icon = "📊"

    source_formats = ["xlsx", "xls", "csv"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for sharing spreadsheets as polished PDF documents."
    priority = 80
    quality = 90
    compatibility = 85
    estimated_saving = 10
    badge = "Portable PDF"
    seo_title = "Excel to PDF Converter | Converigo"
    seo_description = "Convert Excel spreadsheets into PDF files quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("ExcelToPDFPlugin only supports XLSX/XLS/CSV -> PDF.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
