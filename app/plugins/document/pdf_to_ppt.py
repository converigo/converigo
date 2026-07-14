"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PDF -> PPT Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class PDFToPPTPlugin(ConverterPlugin):
    slug = "pdf-to-ppt"
    name = "PDF to PPT"
    description = "Convert PDF documents into PowerPoint presentations."
    category = "document"
    engine = "document"
    icon = "📽️"

    source_formats = ["pdf"]
    target_formats = ["ppt", "pptx"]

    goal = "document"
    use_case = "Best for turning PDFs into editable presentation slides."
    priority = 80
    quality = 90
    compatibility = 85
    estimated_saving = 10
    badge = "Presentation Export"
    seo_title = "PDF to PPT Converter | Converigo"
    seo_description = "Convert PDF documents into PowerPoint presentations quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFToPPTPlugin only supports PDF -> PPT/PPTX.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
