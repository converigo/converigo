"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PDF -> JPG Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class PDFToJPGPlugin(ConverterPlugin):
    slug = "pdf-to-jpg"
    name = "PDF to JPG"
    description = "Convert PDF documents into JPG images page by page."
    category = "document"
    engine = "document"
    icon = "🖼️"

    source_formats = ["pdf"]
    target_formats = ["jpg", "jpeg"]

    goal = "document"
    use_case = "Best for turning PDF pages into image files for sharing and previewing."
    priority = 80
    quality = 90
    compatibility = 85
    estimated_saving = 10
    badge = "Page Images"
    seo_title = "PDF to JPG Converter | Converigo"
    seo_description = "Convert PDF documents into JPG images quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PDFToJPGPlugin only supports PDF -> JPG.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
