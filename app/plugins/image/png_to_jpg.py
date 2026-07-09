"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0

PNG -> JPG Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class PNGToJPGPlugin(ConverterPlugin):

    slug = "png-to-jpg"

    name = "PNG to JPG"

    description = "Convert PNG images to JPG."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = True

    featured = True

    source_formats = [
        "png",
    ]

    target_formats = [
        "jpg",
        "jpeg",
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
                "PNGToJPGPlugin only supports PNG -> JPG."
            )

        engine = ImageEngine()

        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )