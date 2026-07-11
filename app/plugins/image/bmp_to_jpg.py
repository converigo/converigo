"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

BMP -> JPG Plugin

Converigo Smart Metadata Version
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class BMPToJPGPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "bmp-to-jpg"

    name = "BMP to JPG"

    description = (
        "Convert BMP images to JPG "
        "with smaller file size and wider support."
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
        "bmp",
    ]

    target_formats = [
        "jpg",
        "jpeg",
    ]


    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "compress"

    use_case = (
        "Best for reducing BMP file size "
        "and improving compatibility."
    )


    priority = 70

    quality = 85

    compatibility = 100

    estimated_saving = 80


    badge = "File Size Optimizer"


    # ==========================================
    # SEO
    # ==========================================

    seo_title = (
        "BMP to JPG Converter | Converigo"
    )

    seo_description = (
        "Convert BMP images to JPG "
        "with smaller file size."
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
                "BMPToJPGPlugin only supports BMP -> JPG."
            )


        engine = ImageEngine()


        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )