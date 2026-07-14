"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PPT -> PDF Plugin
"""

from pathlib import Path

from app.engines.document_engine import DocumentEngine
from app.plugins.base import ConverterPlugin


class PPTToPDFPlugin(ConverterPlugin):
    slug = "ppt-to-pdf"
    name = "PPT to PDF"
    description = "Convert PowerPoint presentations into PDF files."
    category = "document"
    engine = "document"
    icon = "📽️"

    source_formats = ["ppt", "pptx"]
    target_formats = ["pdf"]

    goal = "document"
    use_case = "Best for sharing presentations as portable PDF files."
    priority = 80
    quality = 90
    compatibility = 85
    estimated_saving = 10
    badge = "Portable PDF"
    seo_title = "PPT to PDF Converter | Converigo"
    seo_description = "Convert PowerPoint presentations into PDF files quickly and easily."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PPTToPDFPlugin only supports PPT/PPTX -> PDF.")

        engine = DocumentEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
