"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0

PNG -> WEBP Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class PNGToWEBPPlugin(ConverterPlugin):

    slug = "png-to-webp"

    name = "PNG to WEBP"

    description = "Convert PNG images to WEBP."

    category = "image"

    engine = "image"

    source_formats = [
        "png",
    ]

    target_formats = [
        "webp",
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
                "PNGToWEBPPlugin only supports PNG -> WEBP."
            )

        engine = ImageEngine()

        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )