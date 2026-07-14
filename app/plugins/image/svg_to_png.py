"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

SVG -> PNG Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class SVGToPNGPlugin(ConverterPlugin):
    slug = "svg-to-png"
    name = "SVG to PNG"
    description = "Convert SVG graphics into PNG images for compatibility."
    category = "image"
    engine = "image"
    icon = "🖼️"

    source_formats = ["svg"]
    target_formats = ["png"]

    goal = "compatibility"
    use_case = "Best for converting scalable vector graphics into raster images."
    priority = 80
    quality = 90
    compatibility = 100
    estimated_saving = 10
    badge = "Raster Export"
    seo_title = "SVG to PNG Converter | Converigo"
    seo_description = "Convert SVG images into PNG files for broad compatibility."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("SVGToPNGPlugin only supports SVG -> PNG.")

        engine = ImageEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
