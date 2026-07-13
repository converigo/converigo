"""
BMP -> WEBP Plugin

Auto-generated for Phase A
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class BMPToWEBPPlugin(ConverterPlugin):

    slug = "bmp-to-webp"

    name = "BMP to WEBP"

    description = "Convert BMP images to WEBP format for smaller sizes."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = False

    featured = False

    source_formats = ["bmp"]

    target_formats = ["webp"]

    goal = "optimization"

    priority = 55

    quality = 90

    compatibility = 85

    estimated_saving = 20

    seo_title = "BMP to WEBP Converter | Converigo"

    seo_description = "Convert BMP images to WEBP to reduce file size for web use."

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("BMPToWEBPPlugin only supports BMP -> WEBP.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
