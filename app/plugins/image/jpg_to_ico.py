"""
JPG -> ICO Plugin

Auto-generated skeleton for Batch B1
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class JPGToICOPlugin(ConverterPlugin):

    slug = "jpg-to-ico"

    name = "JPG to ICO"

    description = "Convert JPG images to ICO format for favicon and icons."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = True

    featured = False

    source_formats = ["jpg", "jpeg"]

    target_formats = ["ico"]

    priority = 80

    async def convert(self, source_path: Path, target_format: str) -> Path:

        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("JPGToICOPlugin only supports JPG -> ICO.")

        engine = ImageEngine()

        return await engine.convert(source_path=source_path, target_format=target_format)
