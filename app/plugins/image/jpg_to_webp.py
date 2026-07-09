"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 1.0.0

JPG -> WEBP Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class JPGToWEBPPlugin(ConverterPlugin):

    slug = "jpg-to-webp"

    name = "JPG to WEBP"

    description = "Convert JPG images to WEBP."

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
                "JPGToWEBPPlugin only supports JPG -> WEBP."
            )

        engine = ImageEngine()

        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )