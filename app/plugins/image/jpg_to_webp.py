"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

JPG -> WEBP Plugin

Converigo Smart Metadata Version
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class JPGToWEBPPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "jpg-to-webp"

    name = "JPG to WEBP"

    description = (
        "Convert JPG images to WEBP "
        "with smaller file size and high quality."
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
        "jpg",
        "jpeg",
    ]

    target_formats = [
        "webp",
    ]


    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "compress"

    use_case = (
        "Best for websites, faster loading, "
        "and smaller image storage."
    )


    priority = 95

    quality = 95

    compatibility = 95

    estimated_saving = 70


    badge = "Best Choice"

    
    # ==========================================
    # SEO
    # ==========================================

    seo_title = (
        "JPG to WEBP Converter | Converigo"
    )

    seo_description = (
        "Convert JPG images into optimized WEBP format."
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
                "JPGToWEBPPlugin only supports JPG -> WEBP."
            )


        engine = ImageEngine()


        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )