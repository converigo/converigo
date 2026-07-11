"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

WEBP -> PNG Plugin

Converigo Smart Metadata Version
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class WEBPToPNGPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "webp-to-png"

    name = "WEBP to PNG"

    description = (
        "Convert WEBP images to PNG "
        "for editing and lossless quality."
    )

    category = "image"

    engine = "image"

    icon = "🖼️"


    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = False

    featured = False


    # ==========================================
    # Formats
    # ==========================================

    source_formats = [
        "webp",
    ]

    target_formats = [
        "png",
    ]


    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "quality"

    use_case = (
        "Best for editing workflows, "
        "design projects, and lossless images."
    )


    priority = 75

    quality = 100

    compatibility = 90

    estimated_saving = 10


    badge = "Lossless Quality"


    # ==========================================
    # SEO
    # ==========================================

    seo_title = (
        "WEBP to PNG Converter | Converigo"
    )

    seo_description = (
        "Convert WEBP images to PNG "
        "for editing and lossless quality."
    )


    # ==========================================
    # Conversion
    # ==========================================

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
                "WEBPToPNGPlugin only supports WEBP -> PNG."
            )


        engine = ImageEngine()


        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )