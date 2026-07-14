"""
Project : Converigo
Author  : Archive Cluster - Growth Sprint
Version : 3.0.0

ZIP -> Extract Plugin
"""

from pathlib import Path

from app.engines.archive_engine import ArchiveEngine
from app.plugins.base import ConverterPlugin


class ZIPExtractPlugin(ConverterPlugin):

    # ==========================================
    # Identity
    # ==========================================

    slug = "zip-extract"
    name = "ZIP Extract"
    description = "Extract files from ZIP archives safely."
    category = "archive"
    engine = "archive"
    icon = "📦"

    # ==========================================
    # Homepage Metadata
    # ==========================================

    popular = True
    featured = True

    # ==========================================
    # Formats
    # ==========================================

    source_formats = ["zip"]
    target_formats = ["zip"]

    # ==========================================
    # Recommendation Metadata
    # ==========================================

    goal = "extraction"
    use_case = "Best when users need to extract files from ZIP archives quickly."
    priority = 95
    quality = 95
    compatibility = 100
    estimated_saving = 0
    badge = "Most Popular"

    # ==========================================
    # SEO
    # ==========================================

    seo_title = "ZIP File Extractor | Converigo"
    seo_description = "Extract files from ZIP archives online. Fast, free, and secure."

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
                "ZIPExtractPlugin only supports ZIP extraction."
            )

        engine = ArchiveEngine()
        return await engine.convert(
            source_path=source_path,
            target_format=target_format,
        )
