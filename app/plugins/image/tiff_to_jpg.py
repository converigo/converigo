"""
TIFF -> JPG Plugin

Auto-generated skeleton for Batch B1
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class TIFFToJPGPlugin(ConverterPlugin):

    slug = "tiff-to-jpg"

    name = "TIFF to JPG"

    description = "Convert TIFF images to JPG format for publishing and web."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = False

    featured = False

    source_formats = ["tiff"]

    target_formats = ["jpg", "jpeg"]

    priority = 70

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("TIFFToJPGPlugin only supports TIFF -> JPG.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
