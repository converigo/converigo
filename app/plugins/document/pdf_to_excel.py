"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PDF -> Excel Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class PDFToExcelPlugin(ConverterPlugin):
    slug = "pdf-to-excel"
    name = "PDF to Excel"
    description = "Convert PDF documents into spreadsheet-friendly Excel files."
    category = "document"
    engine = "document"
    icon = "📊"

    source_formats = ["pdf"]
    target_formats = ["xlsx", "xls"]

    goal = "document"
    use_case = "Best for extracting tabular data from PDFs into Excel."
    priority = 80
    quality = 90
    compatibility = 85
    estimated_saving = 10
    badge = "Spreadsheet Export"
    seo_title = "PDF to Excel Converter | Converigo"
    seo_description = "Convert PDF documents into Excel spreadsheets quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFToExcelPlugin only supports PDF -> XLSX/XLS.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
