"""
PNG -> TIFF Plugin

Auto-generated for Phase A
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class PNGToTIFFPlugin(ConverterPlugin):

    slug = "png-to-tiff"

    name = "PNG to TIFF"

    description = "Convert PNG images to TIFF format for high-fidelity outputs."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = False

    featured = False

    source_formats = ["png"]

    target_formats = ["tiff"]

    goal = "archival"

    priority = 45

    quality = 100

    compatibility = 80

    estimated_saving = 0

    seo_title = "PNG to TIFF Converter | Converigo"

    seo_description = "Convert PNG images to TIFF for archival and printing."

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("PNGToTIFFPlugin only supports PNG -> TIFF.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
