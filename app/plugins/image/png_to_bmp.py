"""
PNG -> BMP Plugin

Auto-generated for Phase A
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class PNGToBMPPlugin(ConverterPlugin):

    slug = "png-to-bmp"

    name = "PNG to BMP"

    description = "Convert PNG images to BMP format."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = False

    featured = False

    source_formats = ["png"]

    target_formats = ["bmp"]

    goal = "legacy_compatibility"

    priority = 40

    quality = 90

    compatibility = 90

    estimated_saving = 5

    seo_title = "PNG to BMP Converter | Converigo"

    seo_description = "Convert PNG images to BMP format."

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PNGToBMPPlugin only supports PNG -> BMP.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
