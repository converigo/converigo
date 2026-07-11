"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

WEBP -> JPG Plugin

Converigo Smart Metadata Version
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class WEBPToJPGPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "webp-to-jpg"

    name = "WEBP to JPG"

    description = (
        "Convert WEBP images to JPG "
        "for wider device compatibility."
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
        "webp",
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
        "Best when WEBP images need "
        "support on more applications "
        "and devices."
    )


    priority = 85

    quality = 90

    compatibility = 100

    estimated_saving = 20


    badge = "Universal Format"


    # ==========================================
    # SEO
    # ==========================================

    seo_title = (
        "WEBP to JPG Converter | Converigo"
    )

    seo_description = (
        "Convert WEBP images to JPG "
        "for better compatibility."
    )


    # ==========================================
    # Conversion
    # ==========================================

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