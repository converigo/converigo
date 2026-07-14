"""
TIFF -> PNG Plugin

Auto-generated skeleton for Batch B1
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class TIFFToPNGPlugin(ConverterPlugin):

    slug = "tiff-to-png"

    name = "TIFF to PNG"

    description = "Convert TIFF images to PNG format for web and editing."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = False

    featured = False

    source_formats = ["tiff"]

    target_formats = ["png"]

    priority = 70

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("TIFFToPNGPlugin only supports TIFF -> PNG.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
