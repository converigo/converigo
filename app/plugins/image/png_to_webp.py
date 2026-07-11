"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PNG -> WEBP Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class PNGToWEBPPlugin(ConverterPlugin):

    # Identity

    slug = "png-to-webp"

    name = "PNG to WEBP"

    description = (
        "Convert PNG images to WEBP "
        "with better compression."
    )

    category = "image"

    engine = "image"


    # Format

    source_formats = [
        "png",
    ]

    target_formats = [
        "webp",
    ]


    # Recommendation Metadata

    goal = "compress"

    use_case = (
        "Best for websites and smaller image size."
    )


    priority = 100

    quality = 95

    compatibility = 95

    estimated_saving = 70


    badge = "Best Choice"

    icon = "🖼️"


    # SEO

    seo_title = (
        "PNG to WEBP Converter | Converigo"
    )

    seo_description = (
        "Convert PNG images into optimized WEBP files."
    )


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