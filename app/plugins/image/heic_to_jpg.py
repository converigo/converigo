"""
Project : Converigo
Author  : Pico Lala & ChatGPT
Version : 3.0.0

HEIC -> JPG Plugin
"""

from pathlib import Path

from app.engines.image_engine import ImageEngine
from app.plugins.base import ConverterPlugin


class HEICToJPGPlugin(ConverterPlugin):
    slug = "heic-to-jpg"
    name = "HEIC to JPG"
    description = "Convert HEIC images into JPG format for broader compatibility."
    category = "image"
    engine = "image"
    icon = "🖼️"

    source_formats = ["heic", "heif"]
    target_formats = ["jpg", "jpeg"]

    goal = "compatibility"
    use_case = "Best for making Apple photos compatible with websites and apps."
    priority = 80
    quality = 90
    compatibility = 100
    estimated_saving = 10
    badge = "Cross-platform"
    seo_title = "HEIC to JPG Converter | Converigo"
    seo_description = "Convert HEIC images into JPG format for better compatibility."

    async def convert(
        self,
        source_path: Path,
        target_format: str,
    ) -> Path:
        if not self.supports(source_path.suffix, target_format):
            raise RuntimeError("HEICToJPGPlugin only supports HEIC/HEIF -> JPG.")

        engine = ImageEngine()
        return await engine.convert(source_path=source_path, target_format=target_format)
