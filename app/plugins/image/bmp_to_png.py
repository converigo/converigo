"""
BMP -> PNG Plugin

Auto-generated for Phase A
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class BMPToPNGPlugin(ConverterPlugin):

    slug = "bmp-to-png"

    name = "BMP to PNG"

    description = "Convert BMP images to PNG format."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = False

    featured = False

    source_formats = ["bmp"]

    target_formats = ["png"]

    goal = "web_compatibility"

    priority = 50

    quality = 95

    compatibility = 90

    estimated_saving = 5

    seo_title = "BMP to PNG Converter | Converigo"

    seo_description = "Convert BMP images to PNG format."

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("BMPToPNGPlugin only supports BMP -> PNG.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
