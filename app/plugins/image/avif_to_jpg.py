"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

AVIF -> JPG Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class AVIFToJPGPlugin(ConverterPlugin):
    slug = "avif-to-jpg"
    name = "AVIF to JPG"
    description = "Convert AVIF images to JPG format with broad compatibility."
    category = "image"
    engine = "image"
    icon = "🖼️"
    popular = True
    featured = False
    source_formats = ["avif"]
    target_formats = ["jpg", "jpeg"]
    goal = "compatibility"
    use_case = "Best for sharing images with devices and apps that require JPG."
    priority = 80
    quality = 90
    compatibility = 100
    estimated_saving = 20
    badge = "Compatible"
    seo_title = "AVIF to JPG Converter | Converigo"
    seo_description = "Convert AVIF images to JPG quickly and easily."

    async def convert(self, source_path: Path, target_format: str) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("AVIFToJPGPlugin only supports AVIF -> JPG.")

        engine = ImageEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
