"""
WEBP -> ICO Plugin

Auto-generated skeleton for Batch B1
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class WEBPToICOPlugin(ConverterPlugin):

    slug = "webp-to-ico"

    name = "WEBP to ICO"

    description = "Convert WEBP images to ICO format for favicon and icons."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = True

    featured = False

    source_formats = ["webp"]

    target_formats = ["ico"]

    priority = 75

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("WEBPToICOPlugin only supports WEBP -> ICO.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
