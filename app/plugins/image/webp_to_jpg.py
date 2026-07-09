"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0

WEBP -> JPG Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class WEBPToJPGPlugin(ConverterPlugin):

    slug = "webp-to-jpg"

    name = "WEBP to JPG"

    description = "Convert WEBP images to JPG."

    category = "image"

    engine = "image"

    icon = "🖼️"

    popular = True

    featured = False

    source_formats = [
        "webp",
    ]

    target_formats = [
        "jpg",
        "jpeg",
    ]

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ):

        if not self.supports(
            source_path.suffix,
            target_format,
        ):
            raise RuntimeError(
                "WEBPToJPGPlugin only supports WEBP -> JPG."
            )

        engine = ImageEngine()

        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )