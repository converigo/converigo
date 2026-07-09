"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0

JPG -> PNG Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class JPGToPNGPlugin(ConverterPlugin):

    slug = "jpg-to-png"

    name = "JPG to PNG"

    description = "Convert JPG images to PNG."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = True

    featured = False

    source_formats = [
        "jpg",
        "jpeg",
    ]

    target_formats = [
        "png",
    ]

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:

        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            raise RuntimeError(
                "JPGToPNGPlugin only supports JPG -> PNG."
            )

        engine = ImageEngine()

        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )