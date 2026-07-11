"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

JPG -> PDF Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class JPGToPDFPlugin(ConverterPlugin):
    slug = "jpg-to-pdf"
    name = "JPG to PDF"
    description = "Convert JPG images into PDF documents while preserving image quality."
    category = "document"
    engine = "document"
    icon = "📄"

    source_formats = ["jpg", "jpeg"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for turning image files into portable PDF documents."
    priority = 80
    quality = 95
    compatibility = 90
    estimated_saving = 15
    badge = "Portable PDF"
    seo_title = "JPG to PDF Converter | Converigo"
    seo_description = "Convert JPG images into PDF documents with high quality."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("JPGToPDFPlugin only supports JPG -> PDF.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
