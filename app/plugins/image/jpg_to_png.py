"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

JPG -> PNG Plugin

Converigo Smart Metadata Version
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class JPGToPNGPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "jpg-to-png"

    name = "JPG to PNG"

    description = (
        "Convert JPG images to PNG format "
        "for lossless quality and editing."
    )

    category = "image"

    engine = "image"

    icon = "🖼️"


    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = True

    featured = False


    # ==========================================
    # Formats
    # ==========================================

    source_formats = [
        "jpg",
        "jpeg",
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
        "JPG to PNG Converter | Converigo"
    )

    seo_description = (
        "Convert JPG images to PNG "
        "with lossless quality."
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
                "JPGToPNGPlugin only supports JPG -> PNG."
            )


        engine = ImageEngine()


        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )