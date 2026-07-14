"""
WEBP -> TIFF Plugin

Auto-generated skeleton for Batch B1
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class WEBPToTIFFPlugin(ConverterPlugin):

    slug = "webp-to-tiff"

    name = "WEBP to TIFF"

    description = "Convert WEBP images to TIFF format for archival and printing."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = False

    featured = False

    source_formats = ["webp"]

    target_formats = ["tiff"]

    priority = 60

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("WEBPToTIFFPlugin only supports WEBP -> TIFF.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
