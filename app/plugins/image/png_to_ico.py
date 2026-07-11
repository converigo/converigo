"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

PNG -> ICO Plugin

Converigo Smart Metadata Version
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class PNGToICOPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "png-to-ico"

    name = "PNG to ICO"

    description = (
        "Convert PNG images into ICO format "
        "for website and application icons."
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
        "ico",
    ]


    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "icon"

    use_case = (
        "Best for favicon, website icons, "
        "and application shortcuts."
    )


    priority = 70

    quality = 85

    compatibility = 85

    estimated_saving = 20


    badge = "For Icons"


    # ==========================================
    # SEO
    # ==========================================

    seo_title = (
        "PNG to ICO Converter | Converigo"
    )

    seo_description = (
        "Convert PNG images to ICO icons "
        "for websites and applications."
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
                "PNGToICOPlugin only supports PNG -> ICO."
            )


        engine = ImageEngine()


        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )