"""
Project : Convertin
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PNG -> JPG Plugin

Convertin Smart Metadata Version
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class PNGToJPGPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "png-to-jpg"

    name = "PNG to JPG"

    description = (
        "Convert PNG images to JPG format "
        "with wide compatibility."
    )

    category = "image"

    engine = "image"

    icon = "🖼️"


    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = True

    featured = True


    # ==========================================
    # Formats
    # ==========================================

    source_formats = [
        "png",
    ]

    target_formats = [
        "jpg",
        "jpeg",
    ]


    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "compatibility"

    use_case = (
        "Best when users need JPG "
        "support on almost all devices."
    )


    priority = 85

    quality = 90

    compatibility = 100

    estimated_saving = 40


    badge = "Most Compatible"


    # ==========================================
    # SEO
    # ==========================================

    seo_title = (
        "PNG to JPG Converter | Convertin"
    )

    seo_description = (
        "Convert PNG images to JPG "
        "with excellent compatibility."
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
                "PNGToJPGPlugin only supports PNG -> JPG."
            )


        engine = ImageEngine()


        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )